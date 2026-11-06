"""Cek Modul 01 — Dari Klik ke Kode (EC2 dengan for_each, moved, reproducible, bersih)."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .. import kumpul as k
from ..umum import TIPE_PRESET, hasil, sidik_instance

MODUL = "m01"
JUDUL = "Dari Klik ke Kode: Self-Service lewat API"
BATAS_ANGGARAN = 50.0

CEK_LATIHAN = ("instance_ada", "dikelola_kode", "tag_pemilik", "preset_valid", "nama_konvensi",
               "berjalan", "tanpa_ip_publik", "anggaran_ada")
CEK_TUGAS = CEK_LATIHAN + ("dua_peran", "refaktor_tanpa_ganti", "reproducible", "bersih_akhir",
                           "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "stacks/m00-fondasi", "stacks/m01-sandbox",
         "docs/m01/catatan-bukti.md", "bukti/bukti-m01.json"]


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    return {
        "instances": k.instance_modul(api, ident["nim"], MODUL),
        "liar": k.instance_liar(api),
        "anggaran": k.anggaran(api, ident["akun"]),
    }


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    inst = snap.get("instances") or []
    return {
        "waktu": waktu,
        "aktif": bool(inst),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    inst = snap.get("instances") or []
    ada = bool(inst)

    def semua(pred) -> bool:
        return ada and all(pred(i) for i in inst)

    pola = re.compile(rf"^koma-{re.escape(nim)}-m01-[a-z0-9-]+$")
    peran = sorted({i["tags"].get("peran") for i in inst if i["tags"].get("peran")})
    nama_anggaran = f"koma-{nim}-anggaran"
    angg = [b for b in snap.get("anggaran") or [] if b.get("nama") == nama_anggaran]
    angg_ok = bool(angg) and all(0 < b["batas"] <= BATAS_ANGGARAN for b in angg)
    return [
        hasil("instance_ada", ada, f"{len(inst)} instance bertag nim={nim}, modul=m01"),
        hasil("dikelola_kode", semua(lambda i: i["tags"].get("managed-by") == "opentofu"),
              "semua instance bertag managed-by=opentofu"),
        hasil("tag_pemilik", semua(lambda i: i["tags"].get("nim") == nim and i["tags"].get("kelompok") == kel),
              f"tag nim={nim} dan kelompok={kel}"),
        hasil("preset_valid", semua(lambda i: i["tipe"] in TIPE_PRESET),
              "tipe instance t3.micro (kecil) atau t3.small (sedang)"),
        hasil("nama_konvensi", semua(lambda i: bool(pola.match(i["nama"]))),
              f"tag Name berbentuk koma-{nim}-m01-<kunci>"),
        hasil("berjalan", semua(lambda i: i["state"] == "running"), "state running"),
        hasil("tanpa_ip_publik", semua(lambda i: not i.get("ip_publik")), "tidak ada IP publik"),
        hasil("anggaran_ada", angg_ok,
              f"budget {nama_anggaran} ada dengan batas <= USD {BATAS_ANGGARAN:g}"
              if angg_ok else f"budget {nama_anggaran} belum ada atau batasnya > USD {BATAS_ANGGARAN:g} "
              "(apply stacks/m00-fondasi)"),
        hasil("dua_peran", len(peran) >= 2, f"peran berbeda: {peran}"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif")]

    repro = False
    for i, awal in enumerate(aktif):
        for akhir in aktif[i + 1:]:
            a, b = awal["instance"], akhir["instance"]
            if a and a.keys() == b.keys() and all(a[n]["sidik"] == b[n]["sidik"] for n in a) \
                    and all(a[n]["id"] != b[n]["id"] for n in a):
                repro = True
                break
        if repro:
            break

    # Refaktor ke for_each dengan blok moved: instance bertambah, instance lama tetap (id sama).
    refaktor = any(
        len(b["instance"]) > len(a["instance"])
        and any(n in b["instance"] and a["instance"][n]["id"] == b["instance"][n]["id"] for n in a["instance"])
        for a, b in zip(aktif, aktif[1:])
    )
    bersih = bool(aktif) and bool(riwayat) and not riwayat[-1].get("aktif")
    return [
        hasil("refaktor_tanpa_ganti", refaktor,
              "instance lama dipertahankan saat for_each menambah instance baru (blok moved)"),
        hasil("reproducible", repro, "dua potret dengan konfigurasi identik tetapi id instance berbeda"),
        hasil("bersih_akhir", bersih, "potret terakhir: tidak ada instance m01 (sudah destroy)"),
    ]
