"""Cek Modul 08 — Capstone Cloud-Native (image di ECR dari pipeline, ECS Fargate di balik ALB, auto
scaling CPU, canary lewat bobot target group, worker pesanan dari Modul 07, bangun ulang dari nol).

Dinilai dari bukti verifier. Cek riwayat membaca jumlah task stabil, tag image per layanan, dan
bobot listener di setiap potret. Registri image (m08-registri) tidak dihitung sebagai "aktif":
ia sengaja bertahan ketika layanan dibangun ulang dari nol.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil
from . import m07

MODUL = "m08"
JUDUL = "Capstone Cloud-Native"
VERIFIER = True
METRIK_CPU = "ECSServiceAverageCPUUtilization"
POLA_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

CEK_LATIHAN = ("registri_ecr", "layanan_stabil", "lb_sehat", "skala_otomatis", "pesanan_terarsip",
               "skala_keluar", "canary_berbobot")
CEK_TUGAS = CEK_LATIHAN + ("canary_dipromosikan", "bangun_ulang", "image_dari_pipeline", "dikelola_kode",
                           "tag_pemilik", "nama_konvensi", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "layanan", "modules/antrean-arsip", "stacks/m00-pipeline",
         "stacks/m00-verifier", "stacks/m08-registri", "stacks/m08-layanan", ".github/workflows/m08.yml",
         "docs/m08/catatan-bukti.md", "docs/m08/laporan-akhir.md", "bukti/bukti-m08.json"]


def _awalan(ident) -> str:
    return f"koma-{ident['nim']}-m08"


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    aw = _awalan(ident)
    return {
        "registri": k.registri(api, aw + "-api"),
        "ecs": k.layanan_ecs(api, aw),
        "alb": k.alb_bernama(api, aw, aw + "-"),
        "topik": k.topik_awalan(api, aw + "-prod-"),
        "antrean": k.antrean_awalan(api, aw + "-prod-"),
        "fungsi": k.fungsi_awalan(api, aw + "-prod-"),
        "bucket": k.bucket_saya(api, aw + "-prod-", prefix_objek="arsip/"),
        "jejak": k.jejak_pipeline(api, ident["nim"], modul="m08", sumber_acara=("ecr.amazonaws.com",)),
        "bertag": [x for x in k.sumber_bertag(api, ident["nim"], MODUL)
                   if ":repository/" not in (x["arn"] or "")],
        "liar": k.instance_liar(api),
    }


def laporan_klien(api, ident: Mapping[str, str], akar: Path | None = None) -> dict[str, Any]:
    """Ringkasan probe, beban, dan pesanan terakhir di .koma/ (informasi, tidak dinilai)."""
    lap: dict[str, Any] = {}
    if akar is not None:
        for nama in ("probe", "beban", "pesan"):
            try:
                lap[nama] = json.loads((akar / ".koma" / f"{nama}-m08.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
    return lap


# ---------------------------------------------------------------------------- pembantu murni

def _tag(image: str | None) -> str | None:
    if not image or ":" not in image.rsplit("/", 1)[-1]:
        return None
    return image.rsplit(":", 1)[-1]


def _layanan(snap, aw: str, jalur: str):
    return next((s for s in ((snap.get("ecs") or {}).get("layanan") or []) if s["nama"] == f"{aw}-{jalur}"), None)


def _tg(snap, aw: str, jalur: str):
    return ((snap.get("alb") or {}).get("target_groups") or {}).get(f"{aw}-{jalur}")


def _bobot(snap, aw: str, jalur: str) -> int:
    alb, tg = snap.get("alb") or {}, _tg(snap, aw, jalur)
    if not tg:
        return 0
    bobot = alb.get("bobot") or {}
    total = sum(bobot.values()) or 1
    return round(100 * bobot.get(tg["arn"], 0) / total)


def _aw_dari_snap(snap) -> str | None:
    cl = (snap.get("ecs") or {}).get("nama")
    if cl:
        return cl
    alb = snap.get("alb")
    if alb:
        return alb["nama"]
    for x in snap.get("topik") or []:
        return re.sub(r"-prod-.*$", "", x["nama"])
    return None


# ---------------------------------------------------------------------------- potret dan cek

def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    aw = _aw_dari_snap(snap)
    stabil = _layanan(snap, aw, "stabil") if aw else None
    canary = _layanan(snap, aw, "canary") if aw else None
    alb = snap.get("alb")
    return {
        "waktu": waktu,
        "aktif": bool((snap.get("ecs") or {}).get("layanan") or alb or snap.get("topik")),
        "instance": {},
        "cluster": (snap.get("ecs") or {}).get("arn"),
        "alb": alb["arn"] if alb else None,
        "stabil": {"tag": _tag(stabil["image"]), "diinginkan": stabil["diinginkan"], "berjalan": stabil["berjalan"],
                   "bobot": _bobot(snap, aw, "stabil")} if stabil else None,
        "canary": {"tag": _tag(canary["image"]), "berjalan": canary["berjalan"],
                   "bobot": _bobot(snap, aw, "canary")} if canary else None,
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    aw = _awalan(ident)
    reg = snap.get("registri")
    reg_ok = bool(reg) and reg["mutabilitas"] == "IMMUTABLE" and reg["pindai"] \
        and any(POLA_SEMVER.match(t) for t in reg["tag"])

    st = _layanan(snap, aw, "stabil")
    dari_reg = bool(st and reg and (st["image"] or "").startswith(reg["uri"] + ":"))
    st_ok = bool(st) and st["jenis"] == "FARGATE" and (st["berjalan"] or 0) >= 1 and dari_reg

    alb = snap.get("alb")
    tg = _tg(snap, aw, "stabil")
    sehat = [t for t in (tg or {}).get("target", []) if t["state"] == "healthy"]
    lb_ok = bool(alb) and alb["state"] == "active" and bool(sehat)

    skala = (st or {}).get("skala") or {}
    skala_ok = bool(st) and (skala.get("maks") or 0) >= 2 and METRIK_CPU in (st or {}).get("kebijakan", [])

    j = m07._jalur(snap, aw, "prod")
    alur_ok, alur_pesan = m07._terhubung(j, "prod")
    arsip = m07._arsip(j)
    pesanan_ok = alur_ok and arsip >= 1

    jejak = snap.get("jejak") or {}
    bertag = snap.get("bertag") or []
    layanan = (snap.get("ecs") or {}).get("layanan") or []
    nama_ok = bool(snap.get("ecs")) and snap["ecs"]["nama"] == aw \
        and all(s["nama"].startswith(aw + "-") for s in layanan) and (not alb or alb["nama"] == aw)

    return [
        hasil("registri_ecr", reg_ok,
              f"registri {reg['nama']} (tag tetap, dipindai) memuat {', '.join(reg['tag'][-4:])}" if reg_ok
              else "registri koma-<nim>-m08-api belum ada, tag dapat ditimpa, pemindaian mati, atau belum ada image bertag versi"),
        hasil("layanan_stabil", st_ok,
              f"{st['nama']} Fargate, {st['berjalan']} task berjalan, image {_tag(st['image'])} dari registri sendiri"
              if st_ok else "layanan -stabil belum berjalan di Fargate dengan image dari registri sendiri"),
        hasil("lb_sehat", lb_ok, f"ALB {aw} aktif, target group stabil punya {len(sehat)} target sehat" if lb_ok
              else "ALB belum aktif atau target group stabil belum punya target sehat"),
        hasil("skala_otomatis", skala_ok,
              f"auto scaling {skala.get('min')}-{skala.get('maks')} task dengan target tracking CPU" if skala_ok
              else "layanan stabil belum punya scalable target (maks >= 2) dengan target tracking CPU"),
        hasil("pesanan_terarsip", pesanan_ok, f"{alur_pesan}; {arsip} objek di arsip/" if pesanan_ok
              else (alur_pesan if not alur_ok else "jalur terhubung, tetapi arsip/ masih kosong (koma pesan <alb_url>)")),
        hasil("image_dari_pipeline", bool(jejak.get("jumlah")),
              f"CloudTrail: {', '.join(jejak['acara'][:3])} oleh role pipeline" if jejak.get("jumlah")
              else "CloudTrail belum mencatat image yang didorong role pipeline (tunggu ±15 menit setelah run)"),
        hasil("dikelola_kode", bool(bertag) and all(x["tags"].get("managed-by") == "opentofu" for x in bertag),
              f"{len(bertag)} resource m08 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(bertag) and all(x["tags"].get("nim") == nim and x["tags"].get("kelompok") == kel
                                                  for x in bertag), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", nama_ok, f"cluster dan ALB bernama {aw}, layanan diawali {aw}-"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def _canary_berbobot(p) -> str | None:
    c, s = p.get("canary"), p.get("stabil")
    if c and s and c.get("tag") and 0 < (c.get("bobot") or 0) < 100 and c["tag"] != s.get("tag"):
        return c["tag"]
    return None


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif")]
    keluar = any(max((p.get("stabil") or {}).get("diinginkan") or 0, (p.get("stabil") or {}).get("berjalan") or 0) >= 2
                 for p in aktif)
    canary = [(i, _canary_berbobot(p)) for i, p in enumerate(riwayat) if _canary_berbobot(p)]
    promosi = any((riwayat[j].get("stabil") or {}).get("tag") == tag
                  and not ((riwayat[j].get("canary") or {}).get("bobot") or 0)
                  for i, tag in canary for j in range(i + 1, len(riwayat)) if riwayat[j].get("aktif"))
    ulang = False
    for i, a in enumerate(riwayat):
        if not (a.get("aktif") and a.get("alb")):
            continue
        for j in range(i + 1, len(riwayat)):
            if riwayat[j].get("aktif"):
                continue
            ulang = any(b.get("aktif") and b.get("alb") and b["alb"] != a["alb"]
                        and (b.get("cek") or {}).get("lb_sehat") and (b.get("cek") or {}).get("layanan_stabil")
                        for b in riwayat[j + 1:])
            break
        if ulang:
            break
    bersih = bool(aktif) and bool(riwayat) and not riwayat[-1].get("aktif")
    return [
        hasil("skala_keluar", keluar, "layanan stabil pernah berskala ke 2 task atau lebih" if keluar
              else "belum ada potret dengan 2 task stabil atau lebih (koma beban <alb_url> --jalur /hitung?n=300000)"),
        hasil("canary_berbobot", bool(canary), f"canary {canary[0][1]} pernah menerima sebagian permintaan" if canary
              else "belum ada potret dengan canary versi lain berbobot di antara 1 dan 99 persen"),
        hasil("canary_dipromosikan", promosi, "versi canary kemudian dilayani layanan stabil tanpa bobot canary"
              if promosi else "belum ada potret setelah canary dengan versi itu di layanan stabil"),
        hasil("bangun_ulang", ulang, "layanan dibongkar lalu dibangun ulang dari nol dan sehat (ALB baru)" if ulang
              else "belum ada urutan potret aktif → kosong → aktif dan sehat dengan ALB baru"),
        hasil("bersih_akhir", bersih, "potret terakhir: tanpa layanan, ALB, dan jalur pesanan m08" if bersih
              else "potret terakhir masih memuat layanan, ALB, atau jalur pesanan m08"),
    ]
