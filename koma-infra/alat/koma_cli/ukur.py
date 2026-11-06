"""Pengukuran dari laptop: `koma probe` (jeda saat alih versi) dan `koma beban` (latensi).

Fungsi ringkasan murni sehingga dapat diuji tanpa jaringan. Hasilnya dicatat di `.koma/` dan ikut
`koma cek` sebagai `laporan_klien` (informasi, tidak dinilai verifier).
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable


def get_versi(url: str, timeout: float = 2.0) -> tuple[bool, str | None, float]:
    """(berhasil, versi, detik) untuk satu GET <url>/versi."""
    mulai = time.monotonic()
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/versi", timeout=timeout) as r:  # noqa: S310
            isi = json.loads(r.read(4096) or b"{}")
            return r.status == 200, str(isi.get("versi")), time.monotonic() - mulai
    except (urllib.error.URLError, OSError, ValueError):
        return False, None, time.monotonic() - mulai


def ringkas_probe(sampel: list[tuple[float, bool, str | None]], selang: float) -> dict[str, Any]:
    """sampel = [(t_detik_sejak_mulai, berhasil, versi)] berurutan."""
    gagal = [s for s in sampel if not s[1]]
    jeda, mulai_gagal, sebelum = 0.0, None, None
    for i, (t, ok, _) in enumerate(sampel):
        if not ok and mulai_gagal is None:
            mulai_gagal = sebelum if sebelum is not None else t
        if ok and mulai_gagal is not None:
            jeda = max(jeda, t - mulai_gagal)
            mulai_gagal = None
        if ok:
            sebelum = t
    if mulai_gagal is not None and sampel:
        jeda = max(jeda, sampel[-1][0] - mulai_gagal)
    versi: dict[str, int] = {}
    for _, ok, v in sampel:
        if ok:
            versi[v or "?"] = versi.get(v or "?", 0) + 1
    alih = next((round(t, 1) for (t, ok, v), (_, ok0, v0) in zip(sampel[1:], sampel)
                 if ok and ok0 and v != v0), None)
    return {"sampel": len(sampel), "gagal": len(gagal), "jeda_terpanjang_detik": round(jeda, 1),
            "selang_detik": selang, "versi": versi, "alih_pada_detik": alih}


def probe(url: str, detik: float, selang: float = 0.5,
          ambil: Callable[[str], tuple[bool, str | None, float]] = get_versi,
          cetak: Callable[[str], None] = print) -> dict[str, Any]:
    sampel: list[tuple[float, bool, str | None]] = []
    mulai = time.monotonic()
    terakhir = None
    while time.monotonic() - mulai < detik:
        t0 = time.monotonic()
        ok, versi, _ = ambil(url)
        t = t0 - mulai
        sampel.append((t, ok, versi))
        status = versi if ok else "GAGAL"
        if status != terakhir:
            cetak(f"  {t:6.1f} dtk  {status}")
            terakhir = status
        time.sleep(max(0.0, selang - (time.monotonic() - t0)))
    return ringkas_probe(sampel, selang)


def persentil(nilai: list[float], p: float) -> float:
    if not nilai:
        return 0.0
    urut = sorted(nilai)
    k = max(0, min(len(urut) - 1, int(round(p / 100 * len(urut) + 0.5)) - 1))
    return urut[k]


def ringkas_beban(lama: list[float], gagal: int, detik: float) -> dict[str, Any]:
    return {"permintaan": len(lama) + gagal, "gagal": gagal, "detik": round(detik, 1),
            "p50_ms": round(persentil(lama, 50) * 1000), "p95_ms": round(persentil(lama, 95) * 1000)}


def beban(url: str, jalur: str, detik: float, paralel: int = 4, timeout: float = 15.0) -> dict[str, Any]:
    alamat = url.rstrip("/") + jalur
    lama: list[float] = []
    gagal = [0]
    kunci = threading.Lock()
    batas = time.monotonic() + detik

    def pekerja():
        while time.monotonic() < batas:
            t0 = time.monotonic()
            try:
                with urllib.request.urlopen(alamat, timeout=timeout) as r:  # noqa: S310
                    r.read(1024)
                    ok = r.status == 200
            except (urllib.error.URLError, OSError):
                ok = False
            with kunci:
                if ok:
                    lama.append(time.monotonic() - t0)
                else:
                    gagal[0] += 1

    mulai = time.monotonic()
    utas = [threading.Thread(target=pekerja, daemon=True) for _ in range(max(1, paralel))]
    for u in utas:
        u.start()
    for u in utas:
        u.join()
    return ringkas_beban(lama, gagal[0], time.monotonic() - mulai)
