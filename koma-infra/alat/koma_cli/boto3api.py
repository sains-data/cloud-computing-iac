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
DAFTAR = {"Filters", "Filter", "Owners", "OwnerIds", "GroupIds", "TagFilters", "Names", "InstanceIds",
          "ResourceTypeFilters", "AttributeNames", "RepositoryNames", "Clusters", "Services", "ResourceIds"}
#: nama parameter boto3 yang tidak mengikuti pola kapitalisasi flag CLI
NAMA_KHUSUS = {"OpenIdConnectProviderArn": "OpenIDConnectProviderArn"}
#: layanan global yang harus dipanggil di us-east-1
GLOBAL = {"budgets": "us-east-1"}
#: nama layanan AWS CLI -> nama klien boto3
KLIEN = {"s3api": "s3"}
#: layanan yang nama parameternya lowerCamelCase (logGroupName, bukan LogGroupName)
CAMEL_KECIL = {"logs", "ecr", "ecs"}


def _nama_param(flag: str) -> str:
    nama = "".join(b.capitalize() for b in flag.lstrip("-").split("-"))
    return NAMA_KHUSUS.get(nama, nama)


def _atribut(teks: str) -> dict[str, str]:
    """"AttributeKey=EventSource,AttributeValue=lambda.amazonaws.com" -> dict tanpa Values."""
    return dict(bagian.partition("=")[::2] for bagian in teks.split(","))


def _pasangan(teks: str) -> dict[str, Any]:
    """"Name=tag:nim,Values=1,2" -> {"Name": "tag:nim", "Values": ["1", "2"]};
    "Key=Name,Option=BeginsWith,Values=/a" -> {"Key": "Name", "Option": "BeginsWith", "Values": ["/a"]}."""
    kepala, _, nilai = teks.partition(",Values=")
    hasil: dict[str, Any] = {}
    for bagian in kepala.split(","):
        kunci, _, isi = bagian.partition("=")
        hasil[kunci] = isi
    hasil["Values"] = [v for v in nilai.split(",") if v]
    return hasil


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
        if nama in ("Filters", "Filter", "TagFilters", "ParameterFilters"):
            params[nama] = [_pasangan(v) for v in nilai]
        elif nama == "LookupAttributes":
            params[nama] = [_atribut(v) for v in nilai]
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
        if layanan in CAMEL_KECIL:
            params = {k[:1].lower() + k[1:]: v for k, v in params.items()}
        try:
            if klien.can_paginate(metode):
                hasil = _gabung(list(klien.get_paginator(metode).paginate(**params)))
            else:
                hasil = _gabung([getattr(klien, metode)(**params)])
        except Exception as exc:  # botocore.exceptions.ClientError dan sejenisnya
            raise GalatAws(f"{layanan} {operasi}: {exc}") from exc
        return json.loads(json.dumps(hasil, default=str))

    def baca_awal(self, bucket: str, key: str, n: int) -> bytes:
        try:
            r = self._client("s3api").get_object(Bucket=bucket, Key=key, Range=f"bytes=0-{n - 1}")
            return r["Body"].read(n)
        except Exception as exc:
            raise GalatAws(f"s3 get-object: {exc}") from exc
