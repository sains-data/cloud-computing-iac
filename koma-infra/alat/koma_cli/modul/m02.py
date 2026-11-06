"""Cek Modul 02 — Server sebagai Kode (cloud-init, AMI panggang, immutable)."""

from __future__ import annotations

from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil, sidik_instance

MODUL = "m02"
JUDUL = "Virtualisasi dan Server sebagai Kode"

CEK_LATIHAN = ("instance_ada", "dikelola_kode", "tag_pemilik", "image_terbit", "api_dari_image",
               "api_sehat")
CEK_TUGAS = CEK_LATIHAN + ("pembangun_dari_publik", "versi_cocok", "sg_terbatas", "nama_konvensi",
                           "immutable", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "stacks/m02-server", "app/koma_api.py",
         "docs/m02/catatan-bukti.md", "bukti/bukti-m02.json"]


def _peran(inst, nama: str) -> list[Mapping[str, Any]]:
    return [i for i in inst if i["tags"].get("peran") == nama]


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    inst = k.instance_modul(api, ident["nim"], MODUL)
    api_inst = _peran(inst, "api")
    sg_ids = sorted({g for i in api_inst for g in i["sg"]})
    probes = {}
    for i in api_inst:
        if i.get("ip_publik"):
            dasar = f"http://{i['ip_publik']}"
            probes[i["id"]] = {"health": k.http_get(dasar + "/health"), "versi": k.http_get(dasar + "/versi")}
    return {
        "instances": inst,
        "images": k.images_modul(api, ident["nim"], MODUL),
        "snapshot_yatim": k.snapshot_yatim(api),
        "sg": k.security_groups(api, sg_ids),
        "probes": probes,
        "liar": k.instance_liar(api),
    }


def _versi_http(snap, inst_id: str) -> str | None:
    isi = ((snap.get("probes") or {}).get(inst_id) or {}).get("versi", {}).get("isi")
    return isi.get("versi") if isinstance(isi, dict) else None


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    inst = snap.get("instances") or []
    imgs = snap.get("images") or []
    api_inst = _peran(inst, "api")
    a = api_inst[0] if api_inst else None
    return {
        "waktu": waktu,
        "aktif": bool(inst or imgs),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
        "image": sorted(im["nama"] for im in imgs),
        "api": {"id": a["id"], "versi": a["tags"].get("versi"), "versi_http": _versi_http(snap, a["id"])}
               if a else None,
        "yatim": len(snap.get("snapshot_yatim") or []),
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    inst = snap.get("instances") or []
    imgs = snap.get("images") or []
    api_inst = _peran(inst, "api")
    pembangun = _peran(inst, "pembangun")
    awalan = f"koma-{nim}-m02-"
    img_ok = [im for im in imgs if im["state"] == "available" and im["nama"].startswith(awalan + "api-")]
    milik = {im["id"] for im in imgs}
    probes = snap.get("probes") or {}

    def sehat(i) -> bool:
        h = (probes.get(i["id"]) or {}).get("health") or {}
        return h.get("kode") == 200 and isinstance(h.get("isi"), dict) and h["isi"].get("status") == "ok"

    def sg_ok() -> tuple[bool, str]:
        grup = snap.get("sg") or []
        if not grup:
            return False, "instance api tanpa security group yang terbaca"
        for g in grup:
            for r in g["masuk"]:
                if "0.0.0.0/0" in r["cidr"] or "::/0" in r["cidr6"]:
                    return False, f"{g['nama']}: port {r['dari']}-{r['ke']} terbuka ke internet"
        port80 = [r for g in grup for r in g["masuk"] if r["dari"] is not None and r["dari"] <= 80 <= (r["ke"] or 0)]
        if not port80 or not all(c.endswith("/32") for r in port80 for c in r["cidr"]) \
                or not any(r["cidr"] for r in port80):
            return False, "port 80 harus dibuka hanya untuk prefix /32 (var.cidr_saya)"
        return True, "port 80 hanya dari /32; tidak ada aturan 0.0.0.0/0"

    versi_ok = bool(api_inst) and all(_versi_http(snap, i["id"]) is not None
                                      and _versi_http(snap, i["id"]) == i["tags"].get("versi") for i in api_inst)
    sg_lulus, sg_pesan = sg_ok() if api_inst else (False, "belum ada instance api")
    nama_ok = bool(inst) and all(i["nama"].startswith(awalan) for i in inst) \
        and all(im["nama"].startswith(awalan) for im in imgs)
    return [
        hasil("instance_ada", bool(api_inst), f"{len(api_inst)} instance peran=api bertag modul=m02"),
        hasil("dikelola_kode", bool(inst) and all(i["tags"].get("managed-by") == "opentofu" for i in inst),
              "semua instance m02 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(inst) and all(i["tags"].get("nim") == nim and i["tags"].get("kelompok") == kel
                                                for i in inst), f"tag nim={nim} dan kelompok={kel}"),
        hasil("image_terbit", bool(img_ok), f"AMI milik sendiri: {[im['nama'] for im in img_ok] or 'belum ada'}"),
        hasil("api_dari_image", bool(api_inst) and all(i["image"] in milik for i in api_inst),
              "instance api diluncurkan dari AMI m02 milik sendiri"),
        hasil("api_sehat", bool(api_inst) and all(sehat(i) for i in api_inst),
              "GET /health -> 200 {status: ok}" if api_inst else "belum ada instance api"),
        hasil("pembangun_dari_publik", bool(pembangun) and all(i["image"] not in milik for i in pembangun),
              "instance pembangun memakai AMI publik (Amazon Linux 2023) + cloud-init"),
        hasil("versi_cocok", versi_ok, "versi dari /versi sama dengan tag versi instance api"),
        hasil("sg_terbatas", sg_lulus, sg_pesan),
        hasil("nama_konvensi", nama_ok, f"Name instance dan nama AMI diawali {awalan}"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif") and p.get("api")]
    immut = any(a["api"]["versi"] != b["api"]["versi"] and a["api"]["id"] != b["api"]["id"]
                and a["api"]["versi"] and b["api"]["versi"]
                for i, a in enumerate(aktif) for b in aktif[i + 1:])
    akhir = riwayat[-1] if riwayat else {}
    pernah = any(p.get("aktif") for p in riwayat)
    bersih = pernah and not akhir.get("aktif") and not akhir.get("yatim")
    pesan = "potret terakhir: tanpa instance, AMI, dan snapshot sisa m02"
    if akhir.get("yatim"):
        pesan = f"masih ada {akhir['yatim']} snapshot sisa AMI (lihat `koma sisa`)"
    return [
        hasil("immutable", immut, "versi baru = instance api baru (bukan diubah di tempat)"),
        hasil("bersih_akhir", bersih, pesan),
    ]
