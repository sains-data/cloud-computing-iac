#!/usr/bin/env python3
"""API contoh Koma (generik untuk semua kasus kelompok) untuk praktikum Komputasi Awan.

Hanya memakai pustaka standar Python, sehingga berjalan di Amazon Linux 2023 (Python 3.9) maupun image cloud Debian
tanpa memasang paket apa pun.

Mode server (bawaan)::

    python3 koma_api.py [--port 8080]

    GET  /health          {"status": "ok"}
    GET  /versi           versi, peran, dan nama host
    GET  /metrics         metrik format Prometheus
    GET  /lambat?ms=500   menunda jawaban (untuk menguji alert latensi)
    GET  /hitung?n=200000 kerja CPU (untuk menguji autoscaling berbasis CPU)
    POST /pesanan         menerima pesanan JSON; diteruskan ke antrian Redis
                          bila KOMA_REDIS diisi (host:port), selain itu dihitung saja

Mode worker::

    python3 koma_api.py worker [--port 8081]

    Mengambil pesanan dari antrian Redis (BRPOP) dan memprosesnya; /metrics dan
    /health tersedia di port yang diberikan.

Konfigurasi lewat environment: KOMA_VERSI, KOMA_PERAN, KOMA_REDIS,
KOMA_ANTRIAN (bawaan "pesanan").
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BUCKETS = (0.05, 0.1, 0.3, 0.5, 1.0, 2.5)


class Metrik:
    """Penghitung dan histogram sederhana, aman dipakai banyak thread."""

    def __init__(self) -> None:
        self._kunci = threading.Lock()
        self.permintaan: dict[tuple[str, int], int] = {}
        self.durasi_bucket: dict[float, int] = {b: 0 for b in BUCKETS}
        self.durasi_jumlah = 0.0
        self.durasi_hitung = 0
        self.pesanan_diterima = 0
        self.pesanan_diproses = 0

    def catat(self, path: str, kode: int, detik: float) -> None:
        with self._kunci:
            self.permintaan[(path, kode)] = self.permintaan.get((path, kode), 0) + 1
            for b in BUCKETS:
                if detik <= b:
                    self.durasi_bucket[b] += 1
            self.durasi_jumlah += detik
            self.durasi_hitung += 1

    def tambah(self, nama: str) -> None:
        with self._kunci:
            setattr(self, nama, getattr(self, nama) + 1)

    def teks(self, versi: str, peran: str) -> str:
        with self._kunci:
            L = ["# HELP koma_info Versi dan peran layanan.", "# TYPE koma_info gauge",
                 f'koma_info{{versi="{versi}",peran="{peran}"}} 1',
                 "# HELP koma_http_requests_total Jumlah permintaan HTTP.",
                 "# TYPE koma_http_requests_total counter"]
            for (path, kode), n in sorted(self.permintaan.items()):
                L.append(f'koma_http_requests_total{{path="{path}",code="{kode}"}} {n}')
            L += ["# HELP koma_http_request_duration_seconds Durasi permintaan HTTP.",
                  "# TYPE koma_http_request_duration_seconds histogram"]
            for b in BUCKETS:
                L.append(f'koma_http_request_duration_seconds_bucket{{le="{b}"}} {self.durasi_bucket[b]}')
            L.append(f'koma_http_request_duration_seconds_bucket{{le="+Inf"}} {self.durasi_hitung}')
            L.append(f"koma_http_request_duration_seconds_sum {self.durasi_jumlah:.6f}")
            L.append(f"koma_http_request_duration_seconds_count {self.durasi_hitung}")
            L += ["# TYPE koma_pesanan_diterima_total counter",
                  f"koma_pesanan_diterima_total {self.pesanan_diterima}",
                  "# TYPE koma_pesanan_diproses_total counter",
                  f"koma_pesanan_diproses_total {self.pesanan_diproses}"]
            return "\n".join(L) + "\n"


# --- klien Redis minimal (RESP) ------------------------------------------------

def resp_perintah(*bagian: str) -> bytes:
    keluar = [f"*{len(bagian)}\r\n".encode()]
    for b in bagian:
        data = b.encode("utf-8")
        keluar.append(b"$%d\r\n%s\r\n" % (len(data), data))
    return b"".join(keluar)


def _baca_baris(f) -> bytes:
    baris = f.readline()
    if not baris:
        raise ConnectionError("koneksi Redis tertutup")
    return baris.rstrip(b"\r\n")


def resp_baca(f):
    baris = _baca_baris(f)
    jenis, isi = baris[:1], baris[1:]
    if jenis == b"+":
        return isi.decode()
    if jenis == b"-":
        raise RuntimeError(isi.decode())
    if jenis == b":":
        return int(isi)
    if jenis == b"$":
        n = int(isi)
        if n < 0:
            return None
        data = f.read(n + 2)
        return data[:-2].decode("utf-8")
    if jenis == b"*":
        n = int(isi)
        return None if n < 0 else [resp_baca(f) for _ in range(n)]
    raise RuntimeError(f"balasan Redis tidak dikenal: {baris!r}")


class Redis:
    def __init__(self, alamat: str, timeout: float = 5.0) -> None:
        host, _, port = alamat.partition(":")
        self.sock = socket.create_connection((host, int(port or 6379)), timeout=timeout)
        self.f = self.sock.makefile("rb")

    def perintah(self, *bagian: str):
        self.sock.sendall(resp_perintah(*bagian))
        return resp_baca(self.f)

    def tutup(self) -> None:
        self.sock.close()


# --- server HTTP -----------------------------------------------------------------

def buat_handler(metrik: Metrik, versi: str, peran: str, redis_alamat: str | None, antrian: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "KomaAPI"

        def log_message(self, fmt, *args):  # log ringkas ke stderr
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

        def _kirim(self, kode: int, isi, tipe: str = "application/json") -> None:
            data = isi.encode() if isinstance(isi, str) else json.dumps(isi).encode()
            self.send_response(kode)
            self.send_header("Content-Type", tipe)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _layani(self, metode: str) -> None:
            mulai = time.monotonic()
            url = urlparse(self.path)
            kode = 404
            try:
                if metode == "GET" and url.path == "/health":
                    kode = 200
                    self._kirim(kode, {"status": "ok"})
                elif metode == "GET" and url.path == "/versi":
                    kode = 200
                    self._kirim(kode, {"versi": versi, "peran": peran, "host": socket.gethostname()})
                elif metode == "GET" and url.path == "/metrics":
                    kode = 200
                    self._kirim(kode, metrik.teks(versi, peran), "text/plain; version=0.0.4")
                elif metode == "GET" and url.path == "/lambat":
                    ms = min(int(parse_qs(url.query).get("ms", ["300"])[0]), 10_000)
                    time.sleep(ms / 1000)
                    kode = 200
                    self._kirim(kode, {"status": "ok", "ms": ms})
                elif metode == "GET" and url.path == "/hitung":
                    n = min(int(parse_qs(url.query).get("n", ["200000"])[0]), 5_000_000)
                    total = sum(i * i for i in range(n))
                    kode = 200
                    self._kirim(kode, {"n": n, "hasil": total % 1_000_007})
                elif metode == "POST" and url.path == "/pesanan":
                    panjang = int(self.headers.get("Content-Length") or 0)
                    pesanan = json.loads(self.rfile.read(panjang) or b"{}")
                    if redis_alamat:
                        r = Redis(redis_alamat)
                        try:
                            r.perintah("LPUSH", antrian, json.dumps(pesanan))
                        finally:
                            r.tutup()
                    metrik.tambah("pesanan_diterima")
                    kode = 202
                    self._kirim(kode, {"status": "diterima"})
                else:
                    self._kirim(kode, {"galat": "tidak ditemukan"})
            except (ValueError, json.JSONDecodeError):
                kode = 400
                self._kirim(kode, {"galat": "permintaan tidak sah"})
            except OSError:
                kode = 503
                self._kirim(kode, {"galat": "antrian tidak tersedia"})
            finally:
                if url.path != "/metrics":
                    metrik.catat(url.path, kode, time.monotonic() - mulai)

        def do_GET(self):
            self._layani("GET")

        def do_POST(self):
            self._layani("POST")

    return Handler


def jalankan_server(port: int, metrik: Metrik, versi: str, peran: str,
                    redis_alamat: str | None, antrian: str) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("0.0.0.0", port), buat_handler(metrik, versi, peran, redis_alamat, antrian))
    srv.daemon_threads = True
    return srv


def loop_worker(metrik: Metrik, redis_alamat: str, antrian: str, berhenti: threading.Event) -> None:
    while not berhenti.is_set():
        try:
            r = Redis(redis_alamat, timeout=10)
            while not berhenti.is_set():
                hasil = r.perintah("BRPOP", antrian, "5")
                if hasil:
                    metrik.tambah("pesanan_diproses")
        except (OSError, ConnectionError, RuntimeError) as e:
            sys.stderr.write(f"worker: {e}; coba lagi 3 detik\n")
            time.sleep(3)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="API contoh Koma")
    ap.add_argument("mode", nargs="?", default="server", choices=["server", "worker"])
    ap.add_argument("--port", type=int, default=None)
    a = ap.parse_args(argv)
    versi = os.environ.get("KOMA_VERSI", "1.0.0")
    peran = os.environ.get("KOMA_PERAN", "api" if a.mode == "server" else "worker")
    redis_alamat = os.environ.get("KOMA_REDIS") or None
    antrian = os.environ.get("KOMA_ANTRIAN", "pesanan")
    metrik = Metrik()
    port = a.port or (8080 if a.mode == "server" else 8081)
    if a.mode == "worker":
        if not redis_alamat:
            print("mode worker butuh KOMA_REDIS (host:port)", file=sys.stderr)
            return 2
        threading.Thread(target=loop_worker, args=(metrik, redis_alamat, antrian, threading.Event()),
                         daemon=True).start()
    srv = jalankan_server(port, metrik, versi, peran, redis_alamat, antrian)
    print(f"koma_api {a.mode} versi {versi} di port {port}", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
