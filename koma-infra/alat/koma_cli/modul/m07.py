"""Cek Modul 07 — Governance, Integrasi, dan Pipeline (dua lingkungan dari satu kode, label tata
kelola, jalur SNS -> SQS -> Lambda -> S3, identitas OIDC GitHub Actions, jejak penerapan pipeline).

Dinilai dari bukti verifier. Lingkungan dikenali dari nama resource (koma-<nim>-m07-<env>-...)
dan dari tag `lingkungan`. Hasil job GitHub Actions tidak terbaca dari akun AWS; yang terbaca
adalah akibatnya: tag `penerap=github-actions` dan kejadian CloudTrail oleh role pipeline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil

MODUL = "m07"
JUDUL = "Governance, Integrasi, dan Pipeline"
VERIFIER = True
LINGKUNGAN = ("dev", "prod")
KELAS_DATA = ("publik", "internal", "rahasia")
LABEL = ("owner", "lingkungan", "cost-center", "data-class")

CEK_LATIHAN = ("dua_lingkungan", "label_wajib", "rahasia_hanya_prod", "alur_terhubung", "arsip_terisi")
CEK_TUGAS = CEK_LATIHAN + ("oidc_github", "role_pipeline", "anggaran_lingkungan", "dlq_menangkap",
                           "diterapkan_pipeline", "jejak_cloudtrail", "dikelola_kode", "tag_pemilik",
                           "nama_konvensi", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "modules/antrean-arsip", "stacks/m00-pipeline", "stacks/m00-verifier",
         "stacks/m07-integrasi", "policy/m07.rego", ".github/workflows/m07.yml",
         "docs/m07/catatan-bukti.md", "bukti/bukti-m07.json"]


def _awalan(ident) -> str:
    return f"koma-{ident['nim']}-m07"


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    aw = _awalan(ident)
    return {
        "topik": k.topik_awalan(api, aw + "-"),
        "antrean": k.antrean_awalan(api, aw + "-"),
        "fungsi": k.fungsi_awalan(api, aw + "-"),
        "bucket": k.bucket_saya(api, aw + "-", prefix_objek="arsip/"),
        "anggaran": [b for b in k.anggaran(api, ident["akun"]) if (b["nama"] or "").startswith(aw + "-")],
        "oidc": k.oidc_github(api),
        "role": k.role_trust(api, f"koma-{ident['nim']}-pipeline"),
        "jejak": k.jejak_pipeline(api, ident["nim"]),
        "bertag": k.sumber_bertag(api, ident["nim"], MODUL),
        "liar": k.instance_liar(api),
    }


def laporan_klien(api, ident: Mapping[str, str], akar: Path | None = None) -> dict[str, Any]:
    """Ringkasan `koma kirim` di .koma/ (informasi, tidak dinilai)."""
    if akar is None:
        return {}
    try:
        return {"kirim": json.loads((akar / ".koma" / "kirim-m07.json").read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------------------- pembantu murni

def _env_dari_nama(aw: str, nama: str) -> str | None:
    m = re.match(rf"^{re.escape(aw)}-(dev|prod)-", nama or "")
    return m.group(1) if m else None


def _cari(daftar, nama):
    return next((x for x in daftar or [] if x["nama"] == nama), None)


def _jalur(snap, aw: str, env: str) -> dict[str, Any]:
    a = f"{aw}-{env}"
    bucket = next((b for b in snap.get("bucket") or [] if b["nama"].startswith(a + "-arsip-")), None)
    return {"topik": _cari(snap.get("topik"), a + "-pesanan"), "antrean": _cari(snap.get("antrean"), a + "-antrean"),
            "gagal": _cari(snap.get("antrean"), a + "-gagal"), "fungsi": _cari(snap.get("fungsi"), a + "-pengarsip"),
            "bucket": bucket}


def _lengkap(j) -> bool:
    return all(j[x] for x in ("topik", "antrean", "fungsi", "bucket"))


def _hidup(j) -> bool:
    return any(j[x] for x in ("topik", "antrean", "fungsi", "bucket"))


def _terhubung(j, env: str) -> tuple[bool, str]:
    if not _lengkap(j):
        return False, f"{env}: jalur belum lengkap (topik, antrean, fungsi, bucket)"
    q, f = j["antrean"], j["fungsi"]
    if not any(s["protokol"] == "sqs" and s["endpoint"] == q["arn"] and s["raw"] for s in j["topik"]["langganan"]):
        return False, f"{env}: topik belum berlangganan antrean {q['nama']} (protokol sqs, raw)"
    if not any(m["sumber"] == q["arn"] and (m["fungsi"] or "").split(":function:")[-1].split(":")[0] == f["nama"]
               and m["state"] == "Enabled" for m in f["pemetaan"]):
        return False, f"{env}: fungsi {f['nama']} belum membaca antrean {q['nama']} (event source mapping Enabled)"
    if env == "prod" and not (j["gagal"] and q["redrive_ke"] == j["gagal"]["arn"]):
        return False, "prod: antrean belum mengalihkan pesan gagal ke DLQ prod (-gagal)"
    return True, f"{env}: topik -> antrean -> fungsi terhubung" + (" + DLQ" if q["redrive_ke"] else "")


def _arsip(j) -> int:
    return sum(1 for kunci in ((j["bucket"] or {}).get("versi_objek") or {}) if kunci.startswith("arsip/"))


def _tag_per_env(snap, nilai: str) -> dict[str, set]:
    hasil_: dict[str, set] = {}
    for x in snap.get("bertag") or []:
        env = x["tags"].get("lingkungan")
        hasil_.setdefault(env, set()).add(x["tags"].get(nilai))
    return hasil_


def _trust_ok(role, oidc) -> tuple[bool, str]:
    if not role:
        return False, "role koma-<nim>-pipeline belum ada (stack m00-pipeline)"
    st = role["trust"].get("Statement", [])
    st = [st] if isinstance(st, dict) else st
    izin = [s for s in st if s.get("Effect") == "Allow"]
    if not izin:
        return False, "trust policy tanpa pernyataan Allow"
    for s in izin:
        fed = (s.get("Principal") or {}).get("Federated")
        if not fed or not str(fed).endswith("/token.actions.githubusercontent.com") \
                or (oidc and fed != oidc["arn"]):
            return False, "role dapat diambil selain lewat provider OIDC GitHub"
        kond = s.get("Condition") or {}
        aud = (kond.get("StringEquals") or {}).get("token.actions.githubusercontent.com:aud")
        if aud != "sts.amazonaws.com" and aud != ["sts.amazonaws.com"]:
            return False, "trust policy tidak mensyaratkan aud = sts.amazonaws.com"
        sub = (kond.get("StringLike") or {}).get("token.actions.githubusercontent.com:sub") \
            or (kond.get("StringEquals") or {}).get("token.actions.githubusercontent.com:sub")
        subs = [sub] if isinstance(sub, str) else list(sub or [])
        if not subs:
            return False, "trust policy tanpa syarat sub: repo GitHub siapa pun dapat mengambil role"
        for v in subs:
            m = re.match(r"^repo:([^/:]+)/([^/:]+):(.+)$", v)
            if not m or "*" in m.group(1) or "*" in m.group(2):
                return False, f"sub {v!r} tidak terikat ke satu repo"
    return True, f"role {role['nama']} hanya untuk {', '.join(sorted(set(subs)))}"


# ---------------------------------------------------------------------------- potret dan cek

def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    aw = None
    for daftar in ("topik", "antrean", "fungsi", "bucket"):
        for x in snap.get(daftar) or []:
            aw = aw or re.sub(r"-(dev|prod)-.*$", "", x["nama"])
    jalur = {env: _jalur(snap, aw, env) for env in LINGKUNGAN} if aw else {}
    bertag = snap.get("bertag") or []
    lengkap = {env: _lengkap(j) for env, j in jalur.items()}
    return {
        "waktu": waktu,
        "aktif": any(_hidup(j) for j in jalur.values()),
        "instance": {},
        "lingkungan": sorted(env for env, ok in lengkap.items() if ok),
        "fungsi": {x["nama"]: x["arn"] for x in snap.get("fungsi") or []},
        "pipeline_semua": bool(bertag) and all(lengkap.get(e) for e in LINGKUNGAN)
        and all(x["tags"].get("penerap") == "github-actions" for x in bertag),
        "penerap": sorted({str(x["tags"].get("penerap")) for x in bertag}),
    }


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    aw = _awalan(ident)
    jalur = {env: _jalur(snap, aw, env) for env in LINGKUNGAN}
    hidup = [env for env in LINGKUNGAN if _hidup(jalur[env])]
    bertag = snap.get("bertag") or []

    dua = all(_lengkap(jalur[e]) for e in LINGKUNGAN)
    kurang = [e for e in LINGKUNGAN if not _lengkap(jalur[e])]

    salah_label = []
    for x in bertag:
        t = x["tags"]
        if t.get("owner") != nim or t.get("lingkungan") not in LINGKUNGAN \
                or not re.fullmatch(r"CC-[0-9]{3}", t.get("cost-center") or "") or t.get("data-class") not in KELAS_DATA:
            salah_label.append(x["arn"])
    cc = _tag_per_env(snap, "cost-center")
    label_ok = bool(bertag) and not salah_label

    rahasia_liar = [x["arn"] for x in bertag
                    if x["tags"].get("data-class") == "rahasia" and x["tags"].get("lingkungan") != "prod"]

    alur = [_terhubung(jalur[e], e) for e in hidup]
    alur_ok = bool(alur) and all(ok for ok, _ in alur)

    arsip = {e: _arsip(jalur[e]) for e in hidup}
    arsip_ok = bool(arsip) and all(n >= 1 for n in arsip.values())

    oidc = snap.get("oidc")
    oidc_ok = bool(oidc) and "sts.amazonaws.com" in oidc["audiens"]
    trust_ok, trust_pesan = _trust_ok(snap.get("role"), oidc)

    anggaran = {b["nama"]: b for b in snap.get("anggaran") or []}
    agg_salah = []
    for e in LINGKUNGAN:
        b = anggaran.get(f"{aw}-{e}")
        nilai = (b or {}).get("saringan", {}).get("TagKeyValue") or []
        if not b or not any(f"user:cost-center${c}" in nilai for c in cc.get(e) or ()):
            agg_salah.append(e)

    gagal = jalur["prod"]["gagal"]
    dlq_ok = bool(gagal) and gagal["pesan"] >= 1

    jejak = snap.get("jejak") or {}
    nama_ok = all(_env_dari_nama(aw, x["nama"]) for d in ("topik", "antrean", "fungsi", "bucket")
                  for x in snap.get(d) or []) and bool(hidup)

    return [
        hasil("dua_lingkungan", dua, "jalur dev dan prod hidup bersamaan" if dua
              else "jalur belum lengkap di: " + ", ".join(kurang)),
        hasil("label_wajib", label_ok, f"{len(bertag)} resource m07 berlabel owner, lingkungan, cost-center, data-class"
              if label_ok else ("label tidak lengkap atau tidak sah pada: " + ", ".join(salah_label[:5]) if salah_label
                                else "belum ada resource m07")),
        hasil("rahasia_hanya_prod", not rahasia_liar, "data rahasia hanya di prod" if not rahasia_liar
              else "data-class rahasia di luar prod: " + ", ".join(rahasia_liar[:5])),
        hasil("alur_terhubung", alur_ok, "; ".join(p for _, p in alur) if alur else "belum ada jalur yang hidup"),
        hasil("arsip_terisi", arsip_ok, ", ".join(f"{e}: {n} objek di arsip/" for e, n in arsip.items())
              + ("" if arsip_ok else " (koma kirim <env>, tunggu beberapa detik)") if arsip else "belum ada bucket arsip"),
        hasil("oidc_github", oidc_ok, "provider OIDC GitHub dengan audiens sts.amazonaws.com" if oidc_ok
              else "provider OIDC token.actions.githubusercontent.com belum ada (stack m00-pipeline)"),
        hasil("role_pipeline", trust_ok, trust_pesan),
        hasil("anggaran_lingkungan", not agg_salah, "budget dev dan prod disaring pada cost-center masing-masing"
              if not agg_salah else "budget belum ada atau saringan cost-center tidak cocok: " + ", ".join(agg_salah)),
        hasil("dlq_menangkap", dlq_ok, f"DLQ prod memuat {gagal['pesan']} pesan" if dlq_ok
              else "DLQ prod kosong atau belum ada (koma kirim prod --rusak 1, tunggu ±2 menit)"),
        hasil("jejak_cloudtrail", bool(jejak.get("jumlah")),
              f"CloudTrail: {', '.join(jejak['acara'][:4])} oleh role pipeline" if jejak.get("jumlah")
              else "CloudTrail belum mencatat perubahan resource m07 oleh role pipeline (tunggu ±15 menit setelah run)"),
        hasil("dikelola_kode", bool(bertag) and all(x["tags"].get("managed-by") == "opentofu" for x in bertag),
              f"{len(bertag)} resource m07 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(bertag) and all(x["tags"].get("nim") == nim and x["tags"].get("kelompok") == kel
                                                  for x in bertag), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", nama_ok, f"nama diawali {aw}-dev- atau {aw}-prod-"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif")]
    pipeline = any(p.get("pipeline_semua") for p in aktif)
    bersih = bool(aktif) and bool(riwayat) and not riwayat[-1].get("aktif")
    return [
        hasil("diterapkan_pipeline", pipeline, "dev dan prod pernah hidup bersamaan, seluruhnya diterapkan pipeline"
              if pipeline else "belum ada potret dengan dev dan prod hidup dan semua resource bertag penerap=github-actions"),
        hasil("bersih_akhir", bersih, "potret terakhir: tanpa topik, antrean, fungsi, dan bucket m07" if bersih
              else "potret terakhir masih memuat jalur m07"),
    ]
