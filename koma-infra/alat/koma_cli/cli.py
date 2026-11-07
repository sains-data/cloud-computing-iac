"""Perintah `koma`. Dijalankan dari akar repo koma-infra (folder yang berisi `alat/`)."""

from __future__ import annotations

import argparse
import inspect
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from . import VERSI, bukti, kumpul, legacy, ukur
from .awsapi import AwsCli, GalatAws
from .modul import TERSEDIA, muat
from .umum import sekarang

AKAR = Path(__file__).resolve().parents[2]
IDENTITAS = AKAR / ".koma" / "identitas.json"
REGION_BAWAAN = "ap-southeast-2"


class Galat(Exception):
    pass


def _cetak(teks: str = "") -> None:
    print(teks, flush=True)


def _identitas() -> dict[str, str]:
    try:
        ident = json.loads(IDENTITAS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Galat("Identitas belum diisi. Jalankan dulu: koma init --nim <NIM> --kelompok <k0N>") from exc
    for kunci in ("nim", "kelompok", "region"):
        if not ident.get(kunci):
            raise Galat(f"{IDENTITAS} tidak memuat `{kunci}`. Jalankan ulang koma init.")
    return ident


def _api_dan_ident() -> tuple[AwsCli, dict[str, str]]:
    ident = _identitas()
    api = AwsCli(ident["region"])
    ident = {**ident, **kumpul.identitas_akun(api)}
    return api, ident


def _git(*args: str, cek: bool = True) -> subprocess.CompletedProcess:
    exe = shutil.which("git")
    if not exe:
        raise Galat("Git tidak ditemukan di PATH.")
    p = subprocess.run([exe, *args], cwd=AKAR, capture_output=True, text=True)
    if cek and p.returncode != 0:
        raise Galat(f"git {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
    return p


def _versi_alat(cmd: list[str]) -> str:
    exe = shutil.which(cmd[0])
    if not exe:
        return "TIDAK DITEMUKAN"
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=20)
        return (p.stdout or p.stderr).strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return "tidak terbaca"


# ---------------------------------------------------------------------------- perintah

def cmd_init(a) -> int:
    if not re.fullmatch(r"[0-9]{8,10}", a.nim):
        raise Galat("NIM harus 8-10 digit angka.")
    if not re.fullmatch(r"k0[0-5]", a.kelompok):
        raise Galat("Kelompok harus k01-k05 (k00 untuk contoh dosen).")
    IDENTITAS.parent.mkdir(parents=True, exist_ok=True)
    lama = {}
    try:
        lama = json.loads(IDENTITAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    baru = {**{k: v for k, v in lama.items() if k in ("verifier_url", "token")},
            "nim": a.nim, "kelompok": a.kelompok, "region": a.region}
    IDENTITAS.write_text(json.dumps(baru, indent=2) + "\n", encoding="utf-8")
    _cetak(f"Identitas ditulis ke {IDENTITAS.relative_to(AKAR)}: NIM {a.nim}, kelompok {a.kelompok}, region {a.region}")
    return 0


def cmd_info(a) -> int:
    ident = _identitas()
    _cetak(f"koma      : {VERSI}")
    _cetak(f"repo      : {AKAR}")
    _cetak(f"NIM       : {ident['nim']}   kelompok: {ident['kelompok']}   region: {ident['region']}")
    _cetak(f"verifier  : {ident.get('verifier_url') or 'belum diatur (koma verifier, mulai Modul 03)'}")
    for nama, cmd in (("tofu", ["tofu", "version"]), ("aws", ["aws", "--version"]), ("git", ["git", "--version"]),
                      ("python", [sys.executable, "--version"])):
        _cetak(f"{nama:<10}: {_versi_alat(cmd)}")
    try:
        akun = kumpul.identitas_akun(AwsCli(ident["region"]))
        _cetak(f"akun AWS  : {akun['akun']}  ({akun['arn']})")
    except GalatAws as exc:
        _cetak(f"akun AWS  : belum masuk -> {exc}")
        return 1
    return 0


def cmd_ip(a) -> int:
    try:
        ip = kumpul.ip_publik()
    except OSError as exc:
        raise Galat(f"IP publik tidak dapat dibaca: {exc}") from exc
    _cetak(f"{ip}/32")
    return 0


def cmd_ambil(a) -> int:
    zpath = Path(a.zip).expanduser()
    if not zpath.is_file():
        raise Galat(f"Berkas {zpath} tidak ditemukan.")
    ditulis, dilewati, diperbarui = [], [], []
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = PurePosixPath(info.filename)
            # ZIP unduhan Workbench berfolder akar koma-mNN-starter/; isinya relatif akar repo.
            if len(rel.parts) > 1 and re.fullmatch(r"koma-m\d\d-(starter|templat)", rel.parts[0]):
                rel = PurePosixPath(*rel.parts[1:])
            if rel.is_absolute() or ".." in rel.parts:
                raise Galat(f"ZIP memuat path tidak sah: {info.filename}")
            tujuan = AKAR.joinpath(*rel.parts)
            alat = rel.parts[0] == "alat"
            if tujuan.exists() and not alat:
                dilewati.append(str(rel))
                continue
            tujuan.parent.mkdir(parents=True, exist_ok=True)
            (diperbarui if tujuan.exists() else ditulis).append(str(rel))
            tujuan.write_bytes(zf.read(info))
    for judul, daftar in (("Ditulis", ditulis), ("Alat diperbarui", diperbarui),
                          ("Dilewati (sudah ada, tidak ditimpa)", dilewati)):
        if daftar:
            _cetak(f"{judul}:")
            for p in daftar:
                _cetak(f"  {p}")
    return 0


def cmd_verifier(a) -> int:
    ident = _identitas()
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+(/.*)?", a.url):
        raise Galat("URL verifier harus https://... (dari dosen).")
    if not re.fullmatch(r"[0-9a-f]{24}", a.token):
        raise Galat("Token harus 24 karakter heksadesimal (dari dosen).")
    IDENTITAS.write_text(json.dumps({**ident, "verifier_url": a.url, "token": a.token}, indent=2) + "\n",
                         encoding="utf-8")
    _cetak("Alamat verifier dan token disimpan di .koma/identitas.json (tidak di-commit).")
    return 0


def _kirim_verifier(ident: dict, mod, laporan: dict) -> dict:
    if not ident.get("verifier_url") or not ident.get("token"):
        raise Galat("Modul ini diperiksa verifier dosen. Jalankan dulu: koma verifier --url <URL> --token <TOKEN>")
    badan = json.dumps({"nim": ident["nim"], "kelompok": ident["kelompok"], "token": ident["token"],
                        "akun": ident["akun"], "region": ident["region"], "modul": mod.MODUL,
                        "versi_koma": VERSI, "laporan_klien": laporan}).encode()
    req = urllib.request.Request(ident["verifier_url"], data=badan, method="POST",
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:  # noqa: S310 (URL dari dosen)
            jawab = json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            pesan = json.loads(exc.read().decode()).get("galat")
        except ValueError:
            pesan = None
        raise Galat(f"verifier menolak ({exc.code}): {pesan or exc.reason}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise Galat(f"verifier tidak dapat dihubungi: {exc}") from exc
    if "bukti" not in jawab:
        raise Galat(f"jawaban verifier tidak sah: {jawab.get('galat') or jawab}")
    return jawab["bukti"]


def cmd_cek(a) -> int:
    mod = muat(a.modul)
    api, ident = _api_dan_ident()
    remote = getattr(mod, "VERIFIER", False) and not a.lokal
    _cetak(f"koma cek {mod.MODUL} - {mod.JUDUL}" + (" (verifier dosen)" if remote else ""))
    _cetak(f"NIM {ident['nim']}, kelompok {ident['kelompok']}, region {ident['region']}")
    path = AKAR / "bukti" / f"bukti-{mod.MODUL}.json"
    if remote:
        laporan = {}
        if hasattr(mod, "laporan_klien"):
            ekstra = {"akar": AKAR} if "akar" in inspect.signature(mod.laporan_klien).parameters else {}
            laporan = mod.laporan_klien(api, ident, **ekstra)
        dok = _kirim_verifier(ident, mod, laporan)
        hasil, riwayat, ringkasan, waktu = dok["hasil"], dok["riwayat"], dok["ringkasan"], dok["dibuat"]
    else:
        if getattr(mod, "VERIFIER", False):
            _cetak("PERINGATAN: --lokal hanya untuk mencari galat; bukti lokal modul ini tidak dinilai.")
            path = AKAR / ".koma" / f"bukti-{mod.MODUL}-lokal.json"
        snap = mod.kumpul(api, ident)
        lama, alasan = bukti.riwayat_lama(bukti.baca(path), ident, mod.MODUL)
        if alasan:
            _cetak(f"Catatan: {alasan}")
        waktu = sekarang()
        hasil, riwayat, ringkasan = bukti.evaluasi(mod, snap, ident, lama, waktu)
        dok = bukti.susun(mod.MODUL, ident, waktu, hasil, ringkasan, riwayat)
    bukti.tulis(path, dok)
    _cetak()
    for h in hasil:
        tanda = "LULUS" if h["lulus"] else "GAGAL"
        peran = "L+T" if h["id"] in mod.CEK_LATIHAN else "T"
        _cetak(f"  [{tanda}] {h['id']:<24} ({peran}) {h['pesan']}")
    _cetak()
    p = riwayat[-1]
    _cetak(f"Potret {len(riwayat)} pada {waktu}: {'aktif' if p.get('aktif') else 'kosong'}, "
           f"{len(p.get('instance') or {})} instance")
    _cetak(f"Latihan lulus: {ringkasan['latihan_lulus']}   Tugas lulus: {ringkasan['tugas_lulus']}")
    _cetak(f"Bukti ditulis: {path.relative_to(AKAR)} (commit berkas ini setiap selesai koma cek)"
           if path.parent.name == "bukti" else f"Bukti lokal (tidak dinilai): {path.relative_to(AKAR)}")
    return 0


def cmd_sehat(a) -> int:
    url = a.url.rstrip("/")
    if not url.startswith("http"):
        url = "http://" + url
    mulai = time.monotonic()
    while True:
        r = kumpul.http_get(url + "/health", timeout=3)
        lama = time.monotonic() - mulai
        if r["kode"] == 200:
            _cetak(f"SEHAT setelah {lama:.1f} detik: {r['isi']}")
            return 0
        if lama >= a.tunggu:
            _cetak(f"BELUM SEHAT setelah {lama:.1f} detik (terakhir: {r['kode'] or r['galat']})")
            return 1
        time.sleep(2)


def cmd_sisa(a) -> int:
    api, ident = _api_dan_ident()
    s = kumpul.sisa(api)
    tetap = [x for x in s["bertag"] if ":budgets::" in x or ":budget/" in x or x.endswith(":role/koma-verifier-ro")
             or (x.startswith("arn:aws:s3:::koma-") and "-tfstate-" in x)]
    lain = [x for x in s["bertag"] if x not in tetap]
    _cetak(f"Region {ident['region']}, akun {ident['akun']}")
    _cetak(f"Resource bertag kursus=komputasi-awan: {len(lain)}")
    for x in lain:
        _cetak(f"  {x}")
    if tetap:
        _cetak(f"Fondasi (boleh tetap ada): {len(tetap)}")
        for x in tetap:
            _cetak(f"  {x}")
    _cetak(f"Instance tanpa tag managed-by: {len(s['liar'])}")
    for i in s["liar"]:
        _cetak(f"  {i['id']} {i['nama']} ({i['state']})")
    if s.get("kunci_menunggu"):
        _cetak(f"Kunci KMS menunggu dihapus (tidak ditagih, hilang sendiri): {len(s['kunci_menunggu'])}")
        for x in s["kunci_menunggu"]:
            _cetak(f"  {x}")
    _cetak(f"Snapshot sisa AMI: {len(s['snapshot_yatim'])}")
    for x in s["snapshot_yatim"]:
        _cetak(f"  {x}")
    _cetak("Catatan: instance yang baru di-terminate bisa masih tampil di daftar bertag sekitar satu jam.")
    return 0 if not (lain or s["liar"] or s["snapshot_yatim"]) else 3


def cmd_arsip(a) -> int:
    mod = muat(a.modul)
    nn = mod.MODUL[1:]
    tag = mod.MODUL
    if _git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}", cek=False).returncode != 0:
        raise Galat(f"Tag {tag} belum ada. Commit semua berkas, lalu: git tag {tag} && git push origin {tag}")
    ada, hilang = [], []
    for p in mod.ARSIP:
        keluar = _git("ls-tree", "-r", "--name-only", tag, "--", p).stdout.strip()
        (ada if keluar else hilang).append(p)
    if hilang:
        _cetak("Peringatan, tidak ada di tag " + tag + ": " + ", ".join(hilang))
    if not ada:
        raise Galat("Tidak ada berkas modul di tag itu.")
    keluar = AKAR / f"koma-module-{nn}.zip"
    _git("archive", "--format=zip", f"--prefix=koma-module-{nn}/", "-o", str(keluar), tag, "--", *ada)
    with zipfile.ZipFile(keluar) as zf:
        nama = zf.namelist()
    terlarang = [n for n in nama if re.search(r"(\.tfstate|terraform\.tfvars$|/\.terraform/|\.koma/|\.tfplan$|\.plan\.json$|kunci-state|/impor\.tf$)", n)]
    if terlarang:
        keluar.unlink()
        raise Galat("Arsip dibatalkan: berkas terlarang ter-commit: " + ", ".join(terlarang))
    _cetak(f"Arsip {keluar.name}: {len(nama)} entri dari tag {tag}. Unggah berkas ini ke Tugas Modul {nn}.")
    return 0


def _tulis_koma(nama: str, isi: dict) -> Path:
    path = AKAR / ".koma" / nama
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**isi, "waktu": sekarang()}, indent=2) + "\n", encoding="utf-8")
    return path


def cmd_legacy(a) -> int:
    api, ident = _api_dan_ident()
    if a.aksi == "buat":
        cidr = f"{kumpul.ip_publik()}/32"
        _cetak(f"Membuat server legacy {legacy.nama(ident)} lewat AWS CLI (HTTP 80 dari {cidr}) ...")
        ada = legacy.buat(api, ident, cidr, legacy.baca_aplikasi(AKAR))
    elif a.aksi == "hapus":
        ada = legacy.hapus(api, ident)
        _cetak(f"Dihapus: instance {ada['instance'] or '-'}, SG {ada['sg'] or '-'}")
        return 0
    else:
        ada = legacy.cari(api, ident)
    if not ada["instance"] and not ada["sg"]:
        _cetak("Legacy belum ada. Jalankan: koma legacy buat")
        return 1
    _cetak(f"Server legacy   : {ada['instance'] or '-'} ({ada['state'] or '-'}), IP publik {ada['ip'] or '-'}")
    _cetak(f"Security group  : {ada['sg'] or '-'}")
    _cetak(f"Aturan HTTP 80  : {ada['aturan'] or '-'} dari {ada['cidr'] or '-'}")
    _cetak(f"Dikelola kode   : {'ya' if ada['dikelola'] else 'belum (belum diimpor)'}")
    _cetak("ID di atas dipakai blok import (Bagian B); cidr_saya harus sama dengan sumber aturan HTTP 80.")
    return 0


def cmd_probe(a) -> int:
    url = a.url if a.url.startswith("http") else "http://" + a.url
    _cetak(f"Probe GET {url}/versi tiap {a.selang} dtk selama {a.detik:.0f} dtk (Ctrl+C untuk berhenti) ...")
    try:
        hasil = ukur.probe(url, a.detik, a.selang, cetak=_cetak)
    except KeyboardInterrupt:
        _cetak("Dihentikan.")
        return 1
    path = _tulis_koma(f"probe-{a.modul}.json", {"url": url, **hasil})
    _cetak(f"Sampel {hasil['sampel']}, gagal {hasil['gagal']}, jeda terpanjang {hasil['jeda_terpanjang_detik']} dtk, "
           f"versi {hasil['versi']}, alih pada detik {hasil['alih_pada_detik']}")
    _cetak(f"Ringkasan: {path.relative_to(AKAR)} (ikut koma cek sebagai laporan_klien)")
    return 0


def cmd_beban(a) -> int:
    url = a.url if a.url.startswith("http") else "http://" + a.url
    _cetak(f"Beban GET {url}{a.jalur} dengan {a.paralel} pekerja selama {a.detik:.0f} dtk ...")
    hasil = ukur.beban(url, a.jalur, a.detik, a.paralel)
    path = _tulis_koma(f"beban-{a.modul}.json", {"url": url, "jalur": a.jalur, **hasil})
    _cetak(f"Permintaan {hasil['permintaan']}, gagal {hasil['gagal']}, p50 {hasil['p50_ms']} ms, p95 {hasil['p95_ms']} ms")
    _cetak(f"Ringkasan: {path.relative_to(AKAR)}")
    return 0


def cmd_kirim(a) -> int:
    api, ident = _api_dan_ident()
    nama = f"koma-{ident['nim']}-m07-{a.lingkungan}-pesanan"
    topik = next((t for t in kumpul.topik_awalan(api, nama) if t["nama"] == nama), None)
    if not topik:
        raise Galat(f"Topik {nama} belum ada. Terapkan stack m07-integrasi untuk lingkungan {a.lingkungan} dulu.")
    cap = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    gerai = ("G-01", "G-02", "G-03", "G-04")
    pesan = [{"id_pesanan": f"P-{cap}-{i:03d}", "gerai": gerai[i % len(gerai)], "total": 25000 + 1500 * i,
              "dibuat": sekarang()} for i in range(1, a.jumlah + 1)]
    pesan += [{"gerai": "G-99", "total": 0, "dibuat": sekarang(), "catatan": "sengaja rusak: tanpa id_pesanan"}
              for _ in range(a.rusak)]
    terkirim = []
    for p in pesan:
        r = api.panggil("sns", "publish", "--topic-arn", topik["arn"], "--message", json.dumps(p))
        terkirim.append({"id_pesanan": p.get("id_pesanan"), "message_id": r.get("MessageId")})
    _cetak(f"Terkirim ke {nama}: {a.jumlah} pesanan sah, {a.rusak} pesan rusak.")
    for t in terkirim:
        _cetak(f"  {t['id_pesanan'] or '(rusak)':<24} {t['message_id']}")
    path = _tulis_koma("kirim-m07.json", {"lingkungan": a.lingkungan, "sah": a.jumlah, "rusak": a.rusak,
                                         "pesan": terkirim})
    _cetak(f"Ringkasan: {path.relative_to(AKAR)}. Objek muncul di arsip/<tanggal>/ dalam beberapa detik;"
           " pesan rusak kembali ke antrean tiap 30 detik (prod: pindah ke DLQ setelah 3 kali).")
    return 0


def _jenis_arn(arn: str) -> str:
    """arn:aws:lambda:…:function:x -> lambda/function; arn:aws:sns:…:x -> sns; arn:aws:s3:::b -> s3."""
    bagian = arn.split(":", 5)
    if len(bagian) < 6:
        return arn
    sisa = bagian[5]
    if ":" in sisa:
        return f"{bagian[2]}/{sisa.split(':', 1)[0]}"
    if "/" in sisa:
        return f"{bagian[2]}/{sisa.split('/', 1)[0]}"
    return bagian[2]


def cmd_showback(a) -> int:
    api, ident = _api_dan_ident()
    r = api.panggil("resourcegroupstaggingapi", "get-resources", "--tag-filters", f"Key=nim,Values={ident['nim']}")
    baris: dict[tuple, dict[str, int]] = {}
    tanpa = []
    for x in r.get("ResourceTagMappingList", []):
        tags = {t["Key"]: t["Value"] for t in x.get("Tags", [])}
        if a.modul != "semua" and tags.get("modul") != a.modul:
            continue
        arn = x.get("ResourceARN", "")
        jenis = _jenis_arn(arn)
        if not tags.get("cost-center"):
            tanpa.append(f"{arn} (modul {tags.get('modul', '-')})")
            continue
        kunci = (tags.get("lingkungan", "-"), tags["cost-center"], tags.get("data-class", "-"))
        baris.setdefault(kunci, {})
        baris[kunci][jenis] = baris[kunci].get(jenis, 0) + 1
    _cetak(f"Showback NIM {ident['nim']}, modul {a.modul} (Resource Groups Tagging API; role IAM tidak terbaca)")
    _cetak(f"{'lingkungan':<11}{'cost-center':<13}{'data-class':<12}resource")
    for (env, cc, kelas), isi in sorted(baris.items()):
        _cetak(f"{env:<11}{cc:<13}{kelas:<12}" + ", ".join(f"{n} {j}" for j, n in sorted(isi.items())))
    _cetak(f"Tak bertuan (tanpa cost-center): {len(tanpa)}")
    for x in tanpa:
        _cetak(f"  {x}")
    return 0


def cmd_pesan(a) -> int:
    url = (a.url if a.url.startswith("http") else "http://" + a.url).rstrip("/")
    gerai = ("G-01", "G-02", "G-03", "G-04")
    hasil_kirim = []
    for i in range(1, a.jumlah + 1):
        badan = json.dumps({"gerai": gerai[i % len(gerai)], "total": 25000 + 1500 * i}).encode()
        req = urllib.request.Request(url + "/pesanan", data=badan, method="POST",
                                     headers={"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310 (ALB milik sendiri)
                isi = json.loads(r.read().decode())
                hasil_kirim.append({"kode": r.status, "id_pesanan": isi.get("id_pesanan"), "versi": isi.get("versi")})
        except urllib.error.HTTPError as exc:
            hasil_kirim.append({"kode": exc.code, "galat": exc.read().decode(errors="replace")[:200]})
        except (urllib.error.URLError, OSError) as exc:
            hasil_kirim.append({"kode": None, "galat": str(exc)})
    for h in hasil_kirim:
        _cetak(f"  {h['kode']}  {h.get('id_pesanan') or h.get('galat')}  {h.get('versi') or ''}")
    sukses = sum(1 for h in hasil_kirim if h["kode"] == 202)
    path = _tulis_koma(f"pesan-{a.modul}.json", {"url": url, "terkirim": sukses, "gagal": len(hasil_kirim) - sukses,
                                                "pesan": hasil_kirim})
    _cetak(f"Diterima layanan: {sukses} dari {len(hasil_kirim)}. Ringkasan: {path.relative_to(AKAR)}")
    return 0 if sukses == len(hasil_kirim) else 1


def buat_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="koma", description=f"Alat praktikum Komputasi Awan (versi {VERSI}).")
    sub = ap.add_subparsers(dest="perintah", required=True)
    p = sub.add_parser("init", help="tulis identitas (NIM, kelompok, region)")
    p.add_argument("--nim", required=True)
    p.add_argument("--kelompok", required=True)
    p.add_argument("--region", default=REGION_BAWAAN)
    p.set_defaults(fn=cmd_init)
    sub.add_parser("info", help="identitas, akun AWS, dan versi alat").set_defaults(fn=cmd_info)
    sub.add_parser("ip", help="IP publik komputer ini sebagai /32").set_defaults(fn=cmd_ip)
    p = sub.add_parser("ambil", help="ekstrak ZIP starter modul tanpa menimpa berkas")
    p.add_argument("zip")
    p.set_defaults(fn=cmd_ambil)
    p = sub.add_parser("cek", help="periksa akun dan tulis bukti/bukti-mNN.json")
    p.add_argument("modul", help=f"modul: {', '.join(TERSEDIA)}")
    p.add_argument("--lokal", action="store_true", help="M03+: periksa di laptop saja (tidak dinilai)")
    p.set_defaults(fn=cmd_cek)
    p = sub.add_parser("verifier", help="simpan alamat verifier dan token dari dosen (M03+)")
    p.add_argument("--url", required=True)
    p.add_argument("--token", required=True)
    p.set_defaults(fn=cmd_verifier)
    p = sub.add_parser("sehat", help="tunggu sampai <url>/health menjawab 200")
    p.add_argument("url")
    p.add_argument("--tunggu", type=float, default=300)
    p.set_defaults(fn=cmd_sehat)
    sub.add_parser("sisa", help="resource praktikum yang masih ada").set_defaults(fn=cmd_sisa)
    p = sub.add_parser("legacy", help="M06: buat, lihat, atau hapus server legacy (dibuat lewat AWS CLI)")
    p.add_argument("aksi", choices=["buat", "info", "hapus"])
    p.set_defaults(fn=cmd_legacy)
    p = sub.add_parser("probe", help="M06: GET <url>/versi berkala, ukur jeda terpanjang saat alih versi")
    p.add_argument("url")
    p.add_argument("--detik", type=float, default=120)
    p.add_argument("--selang", type=float, default=0.5)
    p.add_argument("--modul", default="m06")
    p.set_defaults(fn=cmd_probe)
    p = sub.add_parser("beban", help="M06: beban paralel ke <url><jalur> untuk menguji alarm latensi")
    p.add_argument("url")
    p.add_argument("--jalur", default="/lambat?ms=500")
    p.add_argument("--detik", type=float, default=180)
    p.add_argument("--paralel", type=int, default=4)
    p.add_argument("--modul", default="m06")
    p.set_defaults(fn=cmd_beban)
    p = sub.add_parser("kirim", help="M07: terbitkan pesanan sintetis ke topik lingkungan dev/prod")
    p.add_argument("lingkungan", choices=["dev", "prod"])
    p.add_argument("--jumlah", type=int, default=5)
    p.add_argument("--rusak", type=int, default=0, help="tambah N pesan tanpa id_pesanan (berakhir di DLQ prod)")
    p.set_defaults(fn=cmd_kirim)
    p = sub.add_parser("showback", help="M07: resource bertag dikelompokkan per lingkungan dan cost-center")
    p.add_argument("modul", nargs="?", default="m07", help="modul (bawaan m07) atau 'semua'")
    p.set_defaults(fn=cmd_showback)
    p = sub.add_parser("pesan", help="M08: kirim pesanan sintetis ke <url>/pesanan (API di ECS)")
    p.add_argument("url")
    p.add_argument("--jumlah", type=int, default=5)
    p.add_argument("--modul", default="m08")
    p.set_defaults(fn=cmd_pesan)
    p = sub.add_parser("arsip", help="buat koma-module-NN.zip dari tag mNN")
    p.add_argument("modul")
    p.set_defaults(fn=cmd_arsip)
    return ap


def utama(argv: list[str] | None = None) -> int:
    a = buat_parser().parse_args(argv)
    try:
        return a.fn(a)
    except (Galat, GalatAws, ValueError) as exc:
        print(f"koma: {exc}", file=sys.stderr)
        return 2
