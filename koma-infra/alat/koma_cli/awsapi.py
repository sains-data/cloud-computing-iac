"""Pemanggil AWS CLI v2. Semua akses AWS lewat kelas ini agar mudah dipalsukan di uji."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any


class GalatAws(RuntimeError):
    pass


class AwsCli:
    def __init__(self, region: str | None = None):
        self.region = region

    def panggil(self, *args: str, region: bool = True) -> Any:
        exe = shutil.which("aws")
        if not exe:
            raise GalatAws("AWS CLI v2 tidak ditemukan di PATH. Pasang dulu (lihat naskah Modul 01, Persiapan).")
        cmd = [exe, *args, "--output", "json"]
        if region and self.region:
            cmd += ["--region", self.region]
        env = {**os.environ, "AWS_PAGER": ""}
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        except subprocess.TimeoutExpired as exc:
            raise GalatAws(f"aws {' '.join(args[:2])}: waktu habis") from exc
        if p.returncode != 0:
            pesan = (p.stderr or p.stdout).strip().splitlines()
            ringkas = pesan[-1] if pesan else f"kode keluar {p.returncode}"
            if "login" in ringkas.lower() or "expired" in ringkas.lower() or "credentials" in ringkas.lower():
                ringkas += "\n  -> Jalankan `aws login` lalu ulangi."
            raise GalatAws(f"aws {' '.join(args[:2])}: {ringkas}")
        keluar = p.stdout.strip()
        return json.loads(keluar) if keluar else {}
