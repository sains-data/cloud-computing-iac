"""Cek Modul 06 — Migrasi Brownfield dan Observability (impor legacy, blue-green di balik ALB,
alarm, dasbor, log, drift).

Dinilai dari bukti verifier. Banyak cek bergantung pada riwayat potret: impor tanpa mengganti
server, alamat ALB yang sama sebelum dan sesudah alih versi, drift yang muncul lalu hilang dari
server yang sama, dan legacy yang dibongkar setelah lalu lintas pindah. Probe dan beban dari
laptop ikut sebagai laporan_klien (informasi, tidak dinilai).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil, sidik_instance

MODUL = "m06"
JUDUL = "Migrasi Brownfield dan Observability"
VERIFIER = True
TAG_DRIFT = "diubah-manual"

CEK_LATIHAN = ("legacy_diimpor", "lb_sehat", "alih_ke_hijau", "alarm_latensi", "dasbor_ada", "log_masuk")
CEK_TUGAS = CEK_LATIHAN + ("impor_tanpa_ganti", "alamat_tetap", "alarm_pernah_menyala", "drift_terdeteksi",
                           "drift_direkonsiliasi", "legacy_dibongkar", "dikelola_kode", "tag_pemilik",
                           "nama_konvensi", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "app/koma_api.py", "stacks/m00-verifier", "stacks/m06-migrasi",
         "docs/m06/catatan-bukti.md", "bukti/bukti-m06.json"]


def _awalan(ident) -> str:
    return f"koma-{ident['nim']}-m06"


def _log_group(ident) -> str:
    return f"/koma/{ident['nim']}/m06/api"


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    aw = _awalan(ident)
    return {
        "instances": k.instance_modul(api, ident["nim"], MODUL),
        "alb": k.alb_bernama(api, aw, aw + "-"),
        "alarm": k.alarm_awalan(api, aw),
        "dasbor": k.dasbor_awalan(api, aw),
        "log": k.log_group_awalan(api, _log_group(ident)),
        "bertag": k.sumber_bertag(api, ident["nim"], MODUL),
        "liar": k.instance_liar(api),
    }


def laporan_klien(api, ident: Mapping[str, str], akar: Path | None = None) -> dict[str, Any]:
    """Ringkasan probe dan beban di .koma/ serta penanda konsol server hijau (tidak dinilai)."""
    lap: dict[str, Any] = {}
    if akar is not None:
        for nama in ("probe", "beban"):
            p = akar / ".koma" / f"{nama}-m06.json"
            try:
                lap[nama] = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
    lap["penanda"] = {i["id"]: k.penanda_konsol(api, i["id"])
                      for i in k.instance_modul(api, ident["nim"], MODUL) if i["tags"].get("peran") == "hijau"}
    return lap


def _peran(snap, peran):
    return [i for i in snap.get("instances") or [] if i["tags"].get("peran") == peran]


def _tg(snap, akhiran):
    alb = snap.get("alb") or {}
    return next((v for n, v in (alb.get("target_groups") or {}).items() if n.endswith(akhiran)), None)


def _tg_aktif(snap) -> str | None:
    alb = snap.get("alb") or {}
    for peran in ("biru", "hijau"):
        tg = _tg(snap, "-" + peran)
        if tg and alb.get("tujuan") == tg["arn"]:
            return peran
    return None


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    inst = snap.get("instances") or []
    legacy, hijau = _peran(snap, "legacy"), _peran(snap, "hijau")
    alb = snap.get("alb")
    return {
        "waktu": waktu,
        "aktif": bool(inst or alb),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
        "legacy": {"id": legacy[0]["id"], "dikelola": legacy[0]["tags"].get("managed-by") == "opentofu"}
        if legacy else None,
        "hijau": {"id": hijau[0]["id"], "drift": TAG_DRIFT in hijau[0]["tags"]} if hijau else None,
        "alb": alb["arn"] if alb else None,
        "tg_aktif": _tg_aktif(snap),
        "pernah_alarm": any(a["pernah_alarm"] for a in snap.get("alarm") or []),
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    aw = _awalan(ident)
    alb = snap.get("alb")
    aktif = _tg_aktif(snap)
    tg = _tg(snap, "-" + aktif) if aktif else None
    sehat = [t for t in (tg or {}).get("target", []) if t["state"] == "healthy"]
    lb_ok = bool(alb) and alb["state"] == "active" and bool(sehat)
    hijau = _peran(snap, "hijau")
    tg_hijau = _tg(snap, "-hijau")
    hijau_ok = aktif == "hijau" and bool(hijau) and any(
        t["id"] == hijau[0]["id"] and t["state"] == "healthy" for t in (tg_hijau or {}).get("target", []))
    alarm = [a for a in snap.get("alarm") or [] if a["namespace"] == "AWS/ApplicationELB"
             and a["metrik"] == "TargetResponseTime" and alb and a["dimensi"].get("LoadBalancer") == alb["akhiran"]]
    dasbor_ok = aw in (snap.get("dasbor") or [])
    log = next((g for g in snap.get("log") or [] if g["nama"] == _log_group(ident)), None)
    log_ok = bool(log) and bool(log["event_terakhir"])
    milik = snap.get("bertag") or []
    nama_ok = bool(snap.get("instances")) and all(i["nama"].startswith(aw + "-") for i in snap["instances"]) \
        and (not alb or alb["nama"] == aw)
    return [
        hasil("lb_sehat", lb_ok, f"ALB {aw} aktif, target group {aktif} punya {len(sehat)} target sehat" if lb_ok
              else "ALB belum ada, listener belum meneruskan ke target group modul, atau targetnya belum sehat"),
        hasil("alih_ke_hijau", hijau_ok, "listener meneruskan ke target group hijau dan server hijau sehat" if hijau_ok
              else f"lalu lintas masih ke {aktif or 'tidak ada target group'}, atau server hijau belum sehat"),
        hasil("alarm_latensi", bool(alarm), f"alarm {alarm[0]['nama']} ({alarm[0]['statistik']} > {alarm[0]['ambang']} dtk)"
              if alarm else "belum ada alarm TargetResponseTime untuk ALB modul"),
        hasil("dasbor_ada", dasbor_ok, f"dasbor {aw} ada" if dasbor_ok else f"dasbor {aw} belum ada"),
        hasil("log_masuk", log_ok, f"log group {_log_group(ident)} menerima event dari {log['stream']} stream" if log_ok
              else f"log group {_log_group(ident)} belum ada atau belum menerima event"),
        hasil("dikelola_kode", bool(milik) and all(x["tags"].get("managed-by") == "opentofu" for x in milik),
              f"{len(milik)} resource m06 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(milik) and all(x["tags"].get("nim") == nim and x["tags"].get("kelompok") == kel
                                                 for x in milik), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", nama_ok, f"Name server diawali {aw}-, ALB bernama {aw}"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif")]
    leg = [(i, p["legacy"]) for i, p in enumerate(riwayat) if p.get("legacy")]
    diimpor = any(l["dikelola"] for _, l in leg)
    tanpa_ganti = any(not a["dikelola"] and b["dikelola"] and a["id"] == b["id"]
                      for x, (i, a) in enumerate(leg) for j, b in leg[x + 1:] if j > i)
    alamat = any(a.get("tg_aktif") == "biru" and b.get("tg_aktif") == "hijau" and a.get("alb") and a["alb"] == b.get("alb")
                 for i, a in enumerate(aktif) for b in aktif[i + 1:])
    drift_ada = [p for p in aktif if (p.get("hijau") or {}).get("drift")]
    rekon = any((a.get("hijau") or {}).get("drift") and b.get("hijau") and not b["hijau"]["drift"]
                and a["hijau"]["id"] == b["hijau"]["id"]
                for i, a in enumerate(aktif) for b in aktif[i + 1:])
    bongkar = any(p.get("tg_aktif") == "hijau" and not p.get("legacy")
                  and any((q.get("legacy") or {}).get("dikelola") for q in aktif[:i])
                  for i, p in enumerate(aktif))
    alarm_pernah = any(p.get("pernah_alarm") for p in riwayat)
    pernah = bool(aktif)
    bersih = pernah and bool(riwayat) and not riwayat[-1].get("aktif")
    return [
        hasil("legacy_diimpor", diimpor, "server legacy pernah dikelola OpenTofu (diimpor)" if diimpor
              else "server legacy belum pernah tercatat bertag managed-by=opentofu"),
        hasil("impor_tanpa_ganti", tanpa_ganti,
              "server legacy yang sama: sebelum impor tanpa managed-by, sesudahnya dikelola" if tanpa_ganti
              else "belum ada potret server legacy yang sama sebelum dan sesudah impor (koma cek setelah koma legacy buat?)"),
        hasil("alamat_tetap", alamat, "ALB yang sama meneruskan ke biru lalu ke hijau" if alamat
              else "belum ada potret ke biru lalu ke hijau dengan ALB yang sama"),
        hasil("alarm_pernah_menyala", alarm_pernah, "alarm latensi pernah berstatus ALARM" if alarm_pernah
              else "alarm latensi belum pernah berstatus ALARM (koma beban, lalu tunggu beberapa menit)"),
        hasil("drift_terdeteksi", bool(drift_ada), f"tag {TAG_DRIFT} pada server hijau tercatat di potret" if drift_ada
              else f"belum ada potret dengan tag {TAG_DRIFT} pada server hijau"),
        hasil("drift_direkonsiliasi", rekon, f"tag {TAG_DRIFT} hilang dari server hijau yang sama setelah apply" if rekon
              else f"belum ada potret server hijau yang sama tanpa tag {TAG_DRIFT} setelah drift"),
        hasil("legacy_dibongkar", bongkar, "lalu lintas di hijau dan server legacy sudah tidak ada (contract)" if bongkar
              else "belum ada potret dengan lalu lintas di hijau tanpa server legacy (pertahankan_legacy = false)"),
        hasil("bersih_akhir", bersih, "potret terakhir: tanpa server dan ALB m06" if bersih
              else "potret terakhir masih memuat server atau ALB m06"),
    ]
