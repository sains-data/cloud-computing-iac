"""Cek Modul 05 — Keamanan Cloud sebagai Kode (rahasia, IAM, jaringan, bucket, enkripsi state).

Dinilai dari bukti verifier. Semua cek membaca pengaturan, bukan isi rahasia: nilai parameter
SSM tidak pernah diminta, user data hanya diperiksa polanya, dan dari state m05 hanya dibaca
100 byte pertama untuk mengenali formatnya.
"""

from __future__ import annotations

from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil, sidik_instance

MODUL = "m05"
JUDUL = "Keamanan Cloud sebagai Kode"
VERIFIER = True
STATE_KEY = "m05/aman.tfstate"
PORT_ADMIN = (22, 3389)

CEK_LATIHAN = ("blok_publik_akun", "bucket_privat", "sg_terbatas", "rahasia_securestring",
               "userdata_bersih", "iam_minimal", "state_terenkripsi")
CEK_TUGAS = CEK_LATIHAN + ("kms_rotasi", "imdsv2", "rahasia_dirotasi", "dikelola_kode", "tag_pemilik",
                           "nama_konvensi", "bersih_akhir", "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "app/koma_api.py", "policy/m05.rego", "stacks/m00-pagar",
         "stacks/m00-verifier", "stacks/m05-aman", "docs/m05/laporan-audit.md", "bukti/bukti-m05.json"]


def _nama_state(ident) -> str:
    return f"koma-{ident['nim']}-tfstate-{ident['akun']}"


def _nama_laporan(ident) -> str:
    return f"koma-{ident['nim']}-m05-laporan-{ident['akun']}"


def _awalan_parameter(ident) -> str:
    return f"/koma/{ident['nim']}/m05/"


def _api(snap):
    return [i for i in snap.get("instances") or [] if i["tags"].get("peran") == "api"]


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    inst = k.instance_modul(api, ident["nim"], MODUL)
    utama = [i for i in inst if i["tags"].get("peran") == "api"]
    sg_ids = sorted({g for i in utama for g in i["sg"]})
    bertag = k.sumber_bertag(api, ident["nim"], MODUL)
    kunci = [k.kunci_kms(api, x["arn"]) for x in bertag if ":kms:" in x["arn"] and ":key/" in x["arn"]]
    laporan = [b for b in k.bucket_saya(api, _nama_laporan(ident)) if b["nama"] == _nama_laporan(ident)]
    if laporan:
        laporan[0]["kebijakan_publik"] = k.kebijakan_bucket_publik(api, laporan[0]["nama"])
    state = [b for b in k.bucket_saya(api, _nama_state(ident), "m05/") if b["nama"] == _nama_state(ident)]
    return {
        "instances": inst,
        "sgs": k.security_groups(api, sg_ids),
        "user_data": {i["id"]: k.user_data_rahasia(api, i["id"]) for i in utama},
        "profil": {i["id"]: (k.profil_iam(api, i["profil"]) if i.get("profil") else None) for i in utama},
        "bertag": bertag,
        "kunci": kunci,
        "parameter": k.parameter_awalan(api, _awalan_parameter(ident)),
        "laporan": laporan[0] if laporan else None,
        "akun_blok": k.blok_publik_akun(api, ident["akun"]),
        "state": state[0] if state else None,
        "format_state": k.format_state(k.awal_objek(api, _nama_state(ident), STATE_KEY)) if state else "tidak-ada",
        "liar": k.instance_liar(api),
    }


def laporan_klien(api, ident: Mapping[str, str]) -> dict[str, Any]:
    """Dijalankan `koma cek` di laptop: penanda rahasia dimuat dari log konsol server (tidak dinilai)."""
    return {"penanda": {i["id"]: k.penanda_konsol(api, i["id"])
                        for i in k.instance_modul(api, ident["nim"], MODUL) if i["tags"].get("peran") == "api"}}


def _kunci_aktif(snap):
    return [x for x in snap.get("kunci") or [] if x["state"] == "Enabled"]


def _rahasia(snap, ident):
    nama = _awalan_parameter(ident) + "db-password"
    return next((p for p in snap.get("parameter") or [] if p["nama"] == nama), None)


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    inst = snap.get("instances") or []
    api = _api(snap)
    param = next((p for p in snap.get("parameter") or [] if (p["nama"] or "").endswith("/db-password")), None)
    return {
        "waktu": waktu,
        "aktif": bool(inst or snap.get("laporan") or snap.get("parameter") or _kunci_aktif(snap)),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
        "api": api[0]["id"] if api else None,
        "versi_rahasia": param["versi"] if param else None,
        "kunci": [x["id"] for x in _kunci_aktif(snap)],
    }


def _sg_ok(sgs) -> tuple[bool, str]:
    if not sgs:
        return False, "instance api belum punya security group"
    for g in sgs:
        for r in g["masuk"]:
            dunia = "0.0.0.0/0" in r["cidr"] or "::/0" in r["cidr6"]
            semua = r["proto"] == "-1"
            admin = any(r["dari"] is not None and r["dari"] <= p <= (r["ke"] or r["dari"]) for p in PORT_ADMIN)
            if dunia or semua or admin:
                return False, f"{g['id']}: ingress {r['proto']}/{r['dari']}-{r['ke']} terlalu luas atau port admin"
            if r["dari"] == 80 and not all(c.endswith("/32") for c in r["cidr"]):
                return False, f"{g['id']}: port 80 harus dari satu alamat /32"
    return True, "ingress hanya HTTP dari /32, tanpa port admin dan tanpa 0.0.0.0/0"


def _iam_ok(profil) -> tuple[bool, str]:
    if not profil or not profil.get("peran"):
        return False, "instance api tanpa instance profile (atau role tidak terbaca)"
    for r in profil["peran"]:
        if r["terlampir"]:
            return False, f"role {r['nama']} punya kebijakan terkelola terlampir: {', '.join(r['terlampir'])}"
        boleh = [s for s in r["inline"] if s["efek"] == "Allow"]
        for s in boleh:
            if any(a == "*" or a.endswith(":*") for a in s["aksi"]):
                return False, f"role {r['nama']}, kebijakan {s['kebijakan']}: aksi wildcard"
            if "*" in s["resource"]:
                return False, f"role {r['nama']}, kebijakan {s['kebijakan']}: Resource \"*\""
        if not any("ssm:GetParameter" in s["aksi"] for s in boleh):
            return False, f"role {r['nama']} tidak punya izin ssm:GetParameter"
    return True, "role server hanya punya izin sempit (tanpa wildcard, tanpa kebijakan terkelola)"


def _kunci_cocok(kunci_param: str | None, kunci, nim: str) -> bool:
    """KeyId parameter menunjuk kunci m05 (ARN, ID, atau alias koma-<nim>-m05), bukan kunci bawaan SSM."""
    if not kunci_param or kunci_param == "alias/aws/ssm":
        return False
    if kunci_param in (f"alias/koma-{nim}-m05", f"koma-{nim}-m05") or kunci_param.endswith(f":alias/koma-{nim}-m05"):
        return True
    return any(x["id"] and (kunci_param in (x["arn"], x["id"]) or kunci_param.endswith("/" + x["id"])) for x in kunci)


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    api = _api(snap)
    api0 = api[0] if api else None
    blok = snap.get("akun_blok")
    blok_ok = bool(blok) and all(blok.values())
    lap = snap.get("laporan")
    lap_ok = bool(lap) and lap["publik_diblok"] and lap.get("kebijakan_publik") is not True \
        and "aws:kms" in (lap.get("enkripsi") or [])
    sg_ok, sg_pesan = _sg_ok(snap.get("sgs") or [])
    param = _rahasia(snap, ident)
    kunci = snap.get("kunci") or []
    param_ok = bool(param) and param["tipe"] == "SecureString" and _kunci_cocok(param.get("kunci"), kunci, nim)
    ud = (snap.get("user_data") or {}).get(api0["id"]) if api0 else None
    ud_ok = bool(ud) and ud["ada"] and not ud["rahasia"]
    iam_ok, iam_pesan = _iam_ok((snap.get("profil") or {}).get(api0["id"])) if api0 else (False, "instance api belum ada")
    st = snap.get("state")
    fmt = snap.get("format_state")
    state_ok = bool(st) and STATE_KEY in (st.get("versi_objek") or {}) and fmt == "terenkripsi"
    aktif = _kunci_aktif(snap)
    rotasi_ok = bool(aktif) and all(x["pengelola"] == "CUSTOMER" and x["rotasi"] for x in aktif)
    imds_ok = bool(api) and all(i.get("imds") == "required" for i in api)
    versi = (param or {}).get("versi") or 0
    milik = snap.get("bertag") or []
    nama_ok = bool(milik) and all(
        i["nama"].startswith(f"koma-{nim}-m05-") for i in snap.get("instances") or []) \
        and all(g["tags"].get("Name", "").startswith(f"koma-{nim}-m05-") for g in snap.get("sgs") or []) \
        and (not lap or lap["nama"].startswith(f"koma-{nim}-m05-")) \
        and all(p["nama"].startswith(_awalan_parameter(ident)) for p in snap.get("parameter") or [])
    return [
        hasil("blok_publik_akun", blok_ok, "S3 Block Public Access tingkat akun aktif penuh" if blok_ok
              else "blok publik tingkat akun belum aktif penuh (stack m00-pagar)"),
        hasil("bucket_privat", lap_ok,
              f"bucket {_nama_laporan(ident)} privat dan terenkripsi SSE-KMS" if lap_ok
              else "bucket laporan belum ada, belum memblok publik, kebijakannya publik, atau belum SSE-KMS"),
        hasil("sg_terbatas", sg_ok, sg_pesan),
        hasil("rahasia_securestring", param_ok,
              "password database di Parameter Store sebagai SecureString dengan kunci m05" if param_ok
              else f"parameter {_awalan_parameter(ident)}db-password belum ada, bukan SecureString, "
                   "atau tidak memakai kunci KMS m05"),
        hasil("userdata_bersih", ud_ok, "user data server api tanpa nilai rahasia" if ud_ok
              else ("user data server api memuat nilai rahasia" if ud and ud["rahasia"]
                    else "server api atau user data-nya belum ada")),
        hasil("iam_minimal", iam_ok, iam_pesan),
        hasil("state_terenkripsi", state_ok,
              f"{STATE_KEY} ada dan terenkripsi" if state_ok
              else f"{STATE_KEY}: {fmt if st else 'bucket state tidak ditemukan'}"),
        hasil("kms_rotasi", rotasi_ok, "kunci m05 milik sendiri dengan rotasi aktif" if rotasi_ok
              else "kunci KMS m05 belum ada, bukan milik sendiri, atau rotasinya mati"),
        hasil("imdsv2", imds_ok, "server api mewajibkan IMDSv2" if imds_ok else "server api belum mewajibkan IMDSv2"),
        hasil("rahasia_dirotasi", versi >= 2, f"parameter rahasia versi {versi}"),
        hasil("dikelola_kode", bool(milik) and all(x["tags"].get("managed-by") == "opentofu" for x in milik),
              f"{len(milik)} resource m05 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(milik) and all(x["tags"].get("nim") == nim and x["tags"].get("kelompok") == kel
                                                 for x in milik), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", nama_ok, f"Name diawali koma-{nim}-m05-, parameter diawali {_awalan_parameter(ident)}"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pernah = any(p.get("aktif") for p in riwayat)
    bersih = pernah and bool(riwayat) and not riwayat[-1].get("aktif")
    return [hasil("bersih_akhir", bersih, "potret terakhir: tanpa server, bucket laporan, parameter, dan kunci "
                                          "aktif m05 (kunci yang menunggu dihapus boleh)")]
