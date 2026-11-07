"""Cek per modul. Setiap modul menyediakan:

MODUL, JUDUL, CEK_LATIHAN, CEK_TUGAS, ARSIP (path yang masuk ZIP modul),
kumpul(api, ident) -> snap, potret(snap, waktu) -> dict (wajib berisi `aktif`),
periksa(snap, ident), periksa_selalu(snap, ident), periksa_riwayat(riwayat).
Fungsi selain kumpul() murni sehingga dapat dipakai ulang oleh verifier Lambda.
"""

from __future__ import annotations

import importlib
import re
from types import ModuleType

TERSEDIA = ("m01", "m02", "m03", "m04", "m05", "m06", "m07", "m08")


def muat(nama: str) -> ModuleType:
    nama = nama.lower()
    if not re.fullmatch(r"m\d\d", nama) or nama not in TERSEDIA:
        raise ValueError(f"modul {nama!r} belum tersedia di koma ini (tersedia: {', '.join(TERSEDIA)}). "
                         "Perbarui alat dengan `koma ambil` dari starter modul terbaru.")
    return importlib.import_module(f"koma_cli.modul.{nama}")
