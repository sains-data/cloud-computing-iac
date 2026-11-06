"""Cek Modul 04 — Storage dan State sebagai Kode (state S3, volume EBS, bucket berversi).

Dinilai dari bukti verifier: semua cek dibaca dari API (metadata bucket dan daftar versi objek,
tanpa membaca isi objek).
"""

from __future__ import annotations

from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil, sidik_instance

MODUL = "m04"
JUDUL = "Storage dan State sebagai Kode"
VERIFIER = True
STATE_KEY = "m04/data.tfstate"

CEK_LATIHAN = ("state_remote", "volume_data", "instance_db", "bucket_arsip")
CEK_TUGAS = CEK_LATIHAN + ("state_berversi", "arsip_berversi", "dikelola_kode", "tag_pemilik",
                           "nama_konvensi", "volume_selamat", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "stacks/m00-state", "stacks/m00-verifier", "stacks/m04-data",
         "docs/m04/catatan-bukti.md", "bukti/bukti-m04.json"]


def _nama_state(ident) -> str:
    return f"koma-{ident['nim']}-tfstate-{ident['akun']}"


def _nama_arsip(ident) -> str:
    return f"koma-{ident['nim']}-m04-arsip-{ident['akun']}"


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    state = [b for b in k.bucket_saya(api, _nama_state(ident), "m04/") if b["nama"] == _nama_state(ident)]
    arsip = [b for b in k.bucket_saya(api, _nama_arsip(ident), "laporan/") if b["nama"] == _nama_arsip(ident)]
    return {
        "instances": k.instance_modul(api, ident["nim"], MODUL),
        "volumes": k.volumes_modul(api, ident["nim"], MODUL),
        "state": state[0] if state else None,
        "arsip": arsip[0] if arsip else None,
        "liar": k.instance_liar(api),
    }


def laporan_klien(api, ident: Mapping[str, str]) -> dict[str, Any]:
    """Dijalankan `koma cek` di laptop: penanda data dari log konsol server db (tidak dinilai)."""
    return {"penanda": {i["id"]: k.penanda_konsol(api, i["id"])
                        for i in k.instance_modul(api, ident["nim"], MODUL) if i["tags"].get("peran") == "db"}}


def _db(snap):
    return [i for i in snap.get("instances") or [] if i["tags"].get("peran") == "db"]


def _data(snap):
    return [v for v in snap.get("volumes") or [] if v["tags"].get("peran") == "data"]


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    db, data = _db(snap), _data(snap)
    inst = snap.get("instances") or []
    return {
        "waktu": waktu,
        "aktif": bool(inst or data or snap.get("arsip")),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
        "db": db[0]["id"] if db else None,
        "volume": data[0]["id"] if data else None,
        "ukuran_gib": data[0]["ukuran"] if data else None,
        "terpasang_ke": [a["instance"] for a in data[0]["pasang"]] if data else [],
        "versi_state": ((snap.get("state") or {}).get("versi_objek") or {}).get(STATE_KEY, 0),
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    st, ar = snap.get("state"), snap.get("arsip")
    db, data = _db(snap), _data(snap)
    awalan = f"koma-{nim}-m04-"

    def aman(b) -> bool:
        return bool(b) and b["versioning"] == "Enabled" and b["publik_diblok"] and bool(b["enkripsi"])

    state_ok = aman(st) and STATE_KEY in (st or {}).get("versi_objek", {})
    vol = data[0] if data else None
    db0 = db[0] if db else None
    pasang = [a for a in (vol or {}).get("pasang", []) if db0 and a["instance"] == db0["id"]]
    vol_ok = bool(vol) and vol["terenkripsi"] and vol["state"] == "in-use" and bool(pasang) \
        and not any(a["hapus_bersama"] for a in pasang)
    db_ok = bool(db0) and db0["state"] == "running" and not db0.get("ip_publik")
    lc = (ar or {}).get("lifecycle") or []
    arsip_ok = aman(ar) and len([x for x in lc if x["status"] == "Enabled"]) >= 2 \
        and any(x["versi_lama"] for x in lc if x["status"] == "Enabled")
    versi_state = ((st or {}).get("versi_objek") or {}).get(STATE_KEY, 0)
    versi_arsip = max(((ar or {}).get("versi_objek") or {}).values(), default=0)
    milik = list(snap.get("instances") or []) + list(snap.get("volumes") or [])
    tag_ar = (ar or {}).get("tags") or {}
    return [
        hasil("state_remote", state_ok,
              f"bucket state {_nama_state(ident)} berversi, terenkripsi, tidak publik, memuat {STATE_KEY}"
              if state_ok else f"bucket state {_nama_state(ident)} belum lengkap atau belum memuat {STATE_KEY}"),
        hasil("volume_data", vol_ok,
              "volume data terenkripsi, terpasang ke server db, tidak ikut terhapus bersama server"
              if vol_ok else "volume data belum ada, belum terpasang ke server db, atau tidak terenkripsi"),
        hasil("instance_db", db_ok, "server db berjalan tanpa IP publik" if db_ok else "server db belum berjalan"),
        hasil("bucket_arsip", arsip_ok,
              f"bucket arsip berversi, terenkripsi, tidak publik, {len(lc)} aturan lifecycle"
              if arsip_ok else "bucket arsip belum ada atau versioning/enkripsi/blok publik/lifecycle belum lengkap"),
        hasil("state_berversi", versi_state >= 2, f"{versi_state} versi {STATE_KEY} di bucket state"),
        hasil("arsip_berversi", versi_arsip >= 2, f"objek laporan dengan {versi_arsip} versi"),
        hasil("dikelola_kode", bool(milik) and all(o["tags"].get("managed-by") == "opentofu" for o in milik)
              and tag_ar.get("managed-by") == "opentofu",
              "server, volume, dan bucket arsip bertag managed-by=opentofu" if ar
              else "bucket arsip belum ada (Bagian C); server dan volume diperiksa setelahnya"),
        hasil("tag_pemilik", bool(milik) and all(o["tags"].get("nim") == nim and o["tags"].get("kelompok") == kel
                                                 for o in milik), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", bool(milik) and all(o["tags"].get("Name", "").startswith(awalan) for o in milik),
              f"Name diawali {awalan}"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif") and p.get("db") and p.get("volume")]
    selamat = any(a["volume"] == b["volume"] and a["db"] != b["db"]
                  and a["db"] in a.get("terpasang_ke", []) and b["db"] in b.get("terpasang_ke", [])
                  for i, a in enumerate(aktif) for b in aktif[i + 1:])
    pernah = any(p.get("aktif") for p in riwayat)
    bersih = pernah and bool(riwayat) and not riwayat[-1].get("aktif")
    return [
        hasil("volume_selamat", selamat, "server db diganti, volume data yang sama terpasang ke server baru"),
        hasil("bersih_akhir", bersih, "potret terakhir: tanpa server, volume, dan bucket arsip m04 "
                                      "(bucket state tetap ada)"),
    ]
