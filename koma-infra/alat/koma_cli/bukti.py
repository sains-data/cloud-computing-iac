"""Evaluasi satu kali `koma cek` dan berkas bukti `koma-bukti/3`.

Riwayat potret disimpan di dalam berkas bukti. Bila potret saat ini tidak memuat resource
modul (sudah destroy), cek potret diambil dari potret aktif terakhir sehingga bukti akhir
memuat bukti kebenaran infrastruktur sekaligus bukti akun bersih.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from . import SKEMA_BUKTI, VERSI
from .umum import kanonik, ringkas, sha256

ALG = "HMAC-SHA256"
MAKS_RIWAYAT = 60


def evaluasi(mod: ModuleType, snap: Mapping[str, Any], ident: Mapping[str, str],
             riwayat_lama: list[Mapping[str, Any]], waktu: str):
    """Kembalikan (hasil, riwayat_baru, ringkasan)."""
    p = mod.potret(snap, waktu)
    cek_kini = mod.periksa(snap, ident)
    p["cek"] = {h["id"]: h["lulus"] for h in cek_kini}
    riwayat = [*riwayat_lama, p][-MAKS_RIWAYAT:]
    cek_potret = cek_kini
    if not p.get("aktif"):
        terakhir = next((q for q in reversed(riwayat_lama) if q.get("aktif") and q.get("cek")), None)
        if terakhir is not None:
            pesan = {h["id"]: h["pesan"] for h in cek_kini}
            cek_potret = [{"id": c, "lulus": v,
                           "pesan": f"dari potret aktif {terakhir['waktu']}; kini: {pesan.get(c, '')}"}
                          for c, v in terakhir["cek"].items()]
    hasil = cek_potret + mod.periksa_selalu(snap, ident) + mod.periksa_riwayat(riwayat)
    return hasil, riwayat, ringkas(hasil, mod.CEK_LATIHAN, mod.CEK_TUGAS)


def akun_sidik(akun: str) -> str:
    return sha256(akun)[:16]


def baca(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def riwayat_lama(dok: Mapping[str, Any] | None, ident: Mapping[str, str], modul: str) -> tuple[list, str | None]:
    """Riwayat dari bukti sebelumnya, atau [] beserta alasan bila tidak bisa dipakai."""
    if not dok:
        return [], None
    if dok.get("skema") != SKEMA_BUKTI or dok.get("modul") != modul:
        return [], "bukti lama berskema lain; riwayat dimulai ulang"
    if dok.get("nim") != ident["nim"]:
        return [], "bukti lama milik NIM lain; riwayat dimulai ulang"
    if dok.get("akun_sidik") != akun_sidik(ident["akun"]):
        return [], "bukti lama dibuat di akun AWS lain; riwayat dimulai ulang"
    r = dok.get("riwayat")
    return (list(r) if isinstance(r, list) else []), None


def susun(modul: str, ident: Mapping[str, str], waktu: str, hasil: list, ringkasan: dict,
          riwayat: list, sumber: str = "lokal") -> dict[str, Any]:
    return {
        "skema": SKEMA_BUKTI,
        "versi_koma": VERSI,
        "nim": ident["nim"],
        "kelompok": ident["kelompok"],
        "region": ident.get("region"),
        "akun_sidik": akun_sidik(ident["akun"]),
        "modul": modul,
        "dibuat": waktu,
        "sumber": sumber,
        "hasil": hasil,
        "ringkasan": ringkasan,
        "riwayat": riwayat,
        "tanda_tangan": None,
    }


def tandatangani(dok: Mapping[str, Any], kunci: bytes, kid: str) -> dict[str, Any]:
    isi = {k: v for k, v in dok.items() if k != "tanda_tangan"}
    nilai = hmac.new(kunci, kanonik(isi), hashlib.sha256).hexdigest()
    return {**isi, "tanda_tangan": {"alg": ALG, "kid": kid, "nilai": nilai}}


def sah(dok: Mapping[str, Any], kunci_per_kid: Mapping[str, bytes]) -> bool:
    tt = dok.get("tanda_tangan")
    if not isinstance(tt, dict) or tt.get("alg") != ALG:
        return False
    kunci = kunci_per_kid.get(str(tt.get("kid")))
    if kunci is None:
        return False
    isi = {k: v for k, v in dok.items() if k != "tanda_tangan"}
    return hmac.compare_digest(hmac.new(kunci, kanonik(isi), hashlib.sha256).hexdigest(), str(tt.get("nilai", "")))


def tulis(path: Path, dok: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dok, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
