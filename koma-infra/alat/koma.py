#!/usr/bin/env python3
"""Titik masuk `koma` untuk praktikum Komputasi Awan (jalankan dari akar repo koma-infra).

macOS/Linux:  python3 alat/koma.py <perintah>
Windows:      py alat\\koma.py <perintah>
"""

import importlib
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Modul pustaka standar yang dipakai koma. Berkas bernama sama (mis. subprocess.py buatan sendiri
# di alat/, folder di PYTHONPATH, atau paket pip) dimuat lebih dulu dan membuat koma gagal dengan
# galat yang membingungkan, misalnya "module 'subprocess' has no attribute 'run'".
PUSTAKA_STANDAR = ("argparse", "base64", "datetime", "gzip", "hashlib", "hmac", "json", "shutil",
                   "subprocess", "tempfile", "threading", "zipfile", "urllib.request")


def modul_tertimpa(nama_modul=PUSTAKA_STANDAR):
    """Daftar (nama, asal) modul pustaka standar yang tidak dimuat dari instalasi Python."""
    akar = {os.path.normcase(os.path.realpath(p)) for p in (sys.base_prefix, sys.prefix)}
    hasil = []
    for nama in nama_modul:
        try:
            modul = importlib.import_module(nama)
        except Exception as e:  # noqa: BLE001 - berkas penimpa bisa melempar apa saja
            try:
                asal = importlib.util.find_spec(nama).origin
            except Exception:  # noqa: BLE001
                asal = None
            hasil.append((nama, f"{asal or '?'} (gagal diimpor: {type(e).__name__}: {e})"))
            continue
        berkas = getattr(modul, "__file__", None)
        if not berkas:
            continue  # modul bawaan interpreter
        jalur = os.path.normcase(os.path.realpath(berkas))
        bagian = set(jalur.split(os.sep))
        di_python = any(jalur.startswith(a + os.sep) for a in akar)
        if not di_python or "site-packages" in bagian or "dist-packages" in bagian:
            hasil.append((nama, berkas))
    return hasil


def pesan_tertimpa(tertimpa):
    baris = ["koma tidak dapat berjalan: modul pustaka standar Python tertimpa berkas lain.", ""]
    baris += [f"  {nama:<15} -> {asal}" for nama, asal in tertimpa]
    baris += [
        "",
        "Perbaiki sesuai letak berkas di atas, lalu jalankan koma lagi:",
        "  - di folder alat/ atau folder kerja Anda: ganti nama atau hapus berkas/folder itu,",
        "    beserta berkas __pycache__ di sebelahnya;",
        "  - di folder yang tercantum pada PYTHONPATH: kosongkan PYTHONPATH di terminal ini",
        "    (bash/zsh: unset PYTHONPATH; PowerShell: $env:PYTHONPATH = \"\");",
        "  - di site-packages: copot paket pip yang memasangnya (py -m pip uninstall <paket>",
        "    atau python3 -m pip uninstall <paket>).",
        f"Python yang dipakai: {sys.executable}",
    ]
    return "\n".join(baris)


if __name__ == "__main__":
    tertimpa = modul_tertimpa()
    if tertimpa:
        print(pesan_tertimpa(tertimpa), file=sys.stderr)
        sys.exit(3)

    from koma_cli.cli import utama

    sys.exit(utama())
