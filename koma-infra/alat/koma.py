#!/usr/bin/env python3
"""Titik masuk `koma` untuk praktikum Komputasi Awan (jalankan dari akar repo koma-infra).

macOS/Linux:  python3 alat/koma.py <perintah>
Windows:      py alat\\koma.py <perintah>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koma_cli.cli import utama  # noqa: E402

if __name__ == "__main__":
    sys.exit(utama())
