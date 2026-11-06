"""Adaptor boto3 dengan antarmuka AwsCli (`panggil("ec2", "describe-instances", "--filters", ...)`).

Dipakai verifier Lambda agar modul cek yang sama dengan `koma` di laptop berjalan di server
dengan kredensial role `koma-verifier-ro` milik mahasiswa. Hanya bentuk argumen yang dipakai
`kumpul.py` yang didukung.
"""

from __future__ import annotations

import json
from typing import Any

from .awsapi import GalatAws

#: parameter yang menerima daftar
DAFTAR = {"Filters", "Filter", "Owners", "OwnerIds", "GroupIds", "TagFilters", "Names", "InstanceIds"}
#: layanan global yang harus dipanggil di us-east-1
GLOBAL = {"budgets": "us-east-1"}
#: nama layanan AWS CLI -> nama klien boto3
KLIEN = {"s3api": "s3"}


def _nama_param(flag: str) -> str:
    return "".join(b.capitalize() for b in flag.lstrip("-").split("-"))


def _pasangan(teks: str) -> dict[str, Any]:
    """"Name=tag:nim,Values=1,2" -> {"Name": "tag:nim", "Values": ["1", "2"]}."""
    kepala, _, nilai = teks.partition(",Values=")
    kunci, _, isi = kepala.partition("=")
    return {kunci: isi, "Values": [v for v in nilai.split(",") if v]}


def urai(args: tuple[str, ...]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    i = 0
    while i < len(args):
        flag = args[i]
        if not flag.startswith("--"):
            raise GalatAws(f"argumen tak dikenal: {flag}")
        nilai = []
        i += 1
        while i < len(args) and not args[i].startswith("--"):
            nilai.append(args[i])
            i += 1
        nama = _nama_param(flag)
        if nama in ("Filters", "Filter", "TagFilters"):
            params[nama] = [_pasangan(v) for v in nilai]
        elif nama in DAFTAR:
            params[nama] = nilai
        else:
            params[nama] = nilai[0] if nilai else True
    return params


def _gabung(halaman: list[dict[str, Any]]) -> dict[str, Any]:
    hasil: dict[str, Any] = {}
    for h in halaman:
        for k, v in h.items():
            if k == "ResponseMetadata" or k.startswith("Next") or k == "Marker":
                continue
            if isinstance(v, list):
                hasil.setdefault(k, []).extend(v)
            else:
                hasil[k] = v
    return hasil


class Boto3Api:
    def __init__(self, session, region: str):
        self.session = session
        self.region = region
        self._klien: dict[str, Any] = {}

    def _client(self, layanan: str):
        if layanan not in self._klien:
            self._klien[layanan] = self.session.client(KLIEN.get(layanan, layanan),
                                                       region_name=GLOBAL.get(layanan, self.region))
        return self._klien[layanan]

    def panggil(self, *args: str, region: bool = True) -> Any:
        layanan, operasi, sisa = args[0], args[1], args[2:]
        klien = self._client(layanan)
        metode = operasi.replace("-", "_")
        params = urai(sisa)
        try:
            if klien.can_paginate(metode):
                hasil = _gabung(list(klien.get_paginator(metode).paginate(**params)))
            else:
                hasil = _gabung([getattr(klien, metode)(**params)])
        except Exception as exc:  # botocore.exceptions.ClientError dan sejenisnya
            raise GalatAws(f"{layanan} {operasi}: {exc}") from exc
        return json.loads(json.dumps(hasil, default=str))
