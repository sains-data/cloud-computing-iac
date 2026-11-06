"""Fungsi bersama: JSON kanonik, sidik, waktu, dan bentuk hasil cek."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from typing import Any, Mapping

TIPE_PRESET = {"t3.micro": "kecil", "t3.small": "sedang"}


def kanonik(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sekarang() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hasil(id_: str, lulus: bool, pesan: str) -> dict[str, Any]:
    return {"id": id_, "lulus": bool(lulus), "pesan": pesan}


def tag_tetap(tags: Mapping[str, str]) -> dict[str, str]:
    """Tag yang dideklarasikan pengguna (tanpa tag sistem `aws:*`)."""
    return {k: v for k, v in (tags or {}).items() if not k.startswith("aws:")}


def sidik_instance(inst: Mapping[str, Any]) -> str:
    """Hash konfigurasi yang dideklarasikan: sama bila dibuat ulang dari kode yang sama.

    AMI tidak ikut: data source `most_recent` dapat berpindah ke rilis Amazon Linux baru di
    antara dua apply, dan itu bukan perubahan kode mahasiswa.
    """
    inti = {
        "nama": inst.get("nama"),
        "tipe": inst.get("tipe"),
        "tags": tag_tetap(inst.get("tags") or {}),
    }
    return sha256(kanonik(inti))


def ringkas(hasil_cek: list[Mapping[str, Any]], cek_latihan: tuple[str, ...],
            cek_tugas: tuple[str, ...]) -> dict[str, Any]:
    status = {h["id"]: h["lulus"] for h in hasil_cek}
    return {
        "latihan_lulus": all(status.get(c, False) for c in cek_latihan),
        "tugas_lulus": all(status.get(c, False) for c in cek_tugas),
        "skor_latihan": round(sum(bool(status.get(c, False)) for c in cek_latihan) / len(cek_latihan), 4),
    }
