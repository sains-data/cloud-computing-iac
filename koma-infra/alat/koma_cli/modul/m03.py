"""Cek Modul 03 — Jaringan sebagai Kode (VPC, subnet, rute, security group, ALB).

Dinilai dari bukti verifier (sumber `verifier`): semua cek dibaca dari API AWS, tanpa probe
HTTP, karena security group mahasiswa hanya membuka port untuk IP komputernya sendiri.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from .. import kumpul as k
from ..umum import hasil, sidik_instance

MODUL = "m03"
JUDUL = "Jaringan sebagai Kode"
VERIFIER = True

CEK_LATIHAN = ("vpc_ada", "subnet_publik_privat", "rute_benar", "tanpa_nat", "tiga_sg", "instance_privat",
               "lb_sehat")
CEK_TUGAS = CEK_LATIHAN + ("matriks_positif", "matriks_negatif", "stack_terpisah", "dikelola_kode",
                           "tag_pemilik", "nama_konvensi", "siklus_terpisah", "bersih_akhir",
                           "tanpa_instance_liar")

ARSIP = ["TIM.md", "log-keputusan.md", "stacks/m00-verifier", "stacks/m03-network", "stacks/m03-app",
         "app/koma_api.py", "docs/m03/catatan-bukti.md", "bukti/bukti-m03.json"]

#: (asal, tujuan, port) yang harus diizinkan dan yang harus ditolak security group.
POSITIF = (("alb", "web", 80), ("web", "db", 5432))
NEGATIF = (("internet", "web", 80), ("internet", "db", 5432), ("alb", "db", 5432), ("db", "web", 80))


def kumpul(api, ident: Mapping[str, str]) -> dict[str, Any]:
    vpcs = k.vpc_modul(api, ident["nim"], MODUL)
    snap: dict[str, Any] = {"vpcs": vpcs, "instances": k.instance_modul(api, ident["nim"], MODUL),
                            "nat": k.nat_hidup(api), "liar": k.instance_liar(api),
                            "subnets": [], "route_tables": [], "sg": [], "lbs": []}
    for v in vpcs:
        snap["subnets"] += k.subnets(api, v["id"])
        snap["route_tables"] += k.route_tables(api, v["id"])
        snap["sg"] += k.sg_vpc(api, v["id"])
        snap["lbs"] += k.load_balancers(api, v["id"])
    return snap


def laporan_klien(api, ident: Mapping[str, str]) -> dict[str, Any]:
    """Dijalankan `koma cek` di laptop: GET /health ke ALB dari IP praktikan (informasi, tidak dinilai)."""
    hasil_get = {}
    for v in k.vpc_modul(api, ident["nim"], MODUL):
        for lb in k.load_balancers(api, v["id"]):
            hasil_get[lb["nama"]] = k.http_get(f"http://{lb['dns']}/health", timeout=5)
    return {"alb_health": hasil_get}


def potret(snap: Mapping[str, Any], waktu: str) -> dict[str, Any]:
    inst = snap.get("instances") or []
    vpcs = snap.get("vpcs") or []
    lbs = snap.get("lbs") or []
    # Aktif = ada server atau load balancer. Potret yang hanya berisi VPC (di antara destroy app
    # dan destroy network) tidak aktif, sehingga cek potret tetap dibawa dari potret aktif terakhir;
    # sisa VPC tetap menggagalkan bersih_akhir.
    return {
        "waktu": waktu,
        "aktif": bool(inst or lbs),
        "instance": {(i["nama"] or i["id"]): {"id": i["id"], "sidik": sidik_instance(i)} for i in inst},
        "vpc": vpcs[0]["id"] if vpcs else None,
        "cidr": vpcs[0]["cidr"] if vpcs else None,
        "lb": lbs[0]["arn"] if lbs else None,
    }


def _sg_peran(snap) -> dict[str, Mapping[str, Any]]:
    return {g["tags"].get("peran"): g for g in snap.get("sg") or [] if g["tags"].get("peran")}


def _izin(sgs: Mapping[str, Mapping[str, Any]], asal: str, tujuan: str, port: int) -> bool:
    """Apakah SG peran `tujuan` menerima koneksi dari `asal` (peran SG atau 'internet') di `port`."""
    g = sgs.get(tujuan)
    if not g:
        return False
    asal_id = (sgs.get(asal) or {}).get("id")
    for r in g["masuk"]:
        semua_port = r["proto"] == "-1"
        if not semua_port and not (r["dari"] is not None and r["dari"] <= port <= (r["ke"] or r["dari"])):
            continue
        if asal == "internet" and ("0.0.0.0/0" in r["cidr"] or "::/0" in r["cidr6"]):
            return True
        if asal_id and asal_id in r["sg"]:
            return True
    return False


def periksa(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    nim, kel = ident["nim"], ident["kelompok"]
    vpcs = snap.get("vpcs") or []
    subs = snap.get("subnets") or []
    rts = snap.get("route_tables") or []
    inst = snap.get("instances") or []
    lbs = snap.get("lbs") or []
    sgs = _sg_peran(snap)
    awalan = f"koma-{nim}-m03-"

    vpc = vpcs[0] if len(vpcs) == 1 else None
    vpc_ok = bool(vpc) and bool(re.fullmatch(r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}/16", vpc["cidr"] or ""))
    publik = [s for s in subs if s["tags"].get("tier") == "publik"]
    privat = [s for s in subs if s["tags"].get("tier") == "privat"]
    subnet_ok = (len(publik) >= 2 and len(privat) >= 2 and len({s["az"] for s in publik}) >= 2
                 and len({s["az"] for s in privat}) >= 2 and not any(s["ip_publik_otomatis"] for s in privat))

    rt_utama = next((rt for rt in rts if rt["utama"]), None)

    def rt_untuk(subnet_id):
        return next((rt for rt in rts if subnet_id in rt["subnets"]), rt_utama)

    def keluar(rt) -> list[str]:
        return [x["lewat"] or "" for x in (rt or {}).get("rute", []) if x["tujuan"] in ("0.0.0.0/0", "::/0")]

    rute_ok = bool(publik) and bool(privat) \
        and all(any(g.startswith("igw-") for g in keluar(rt_untuk(s["id"]))) for s in publik) \
        and all(not keluar(rt_untuk(s["id"])) for s in privat)

    id_privat = {s["id"] for s in privat}
    web = [i for i in inst if i["tags"].get("peran") == "web"]
    db = [i for i in inst if i["tags"].get("peran") == "db"]
    inst_ok = bool(web) and bool(db) and all(
        i["subnet"] in id_privat and not i.get("ip_publik")
        and (sgs.get(i["tags"]["peran"]) or {}).get("id") in i["sg"] for i in web + db)

    lb = lbs[0] if lbs else None
    sehat = [t for tg in (lb or {}).get("target_groups", []) for t in tg["target"] if t["state"] == "healthy"]
    lb_ok = bool(lb) and lb["state"] == "active" and len(lb["azs"]) >= 2 and bool(sehat)

    pos = [f"{a}->{b}:{p}" for a, b, p in POSITIF if not _izin(sgs, a, b, p)]
    neg = [f"{a}->{b}:{p}" for a, b, p in NEGATIF if _izin(sgs, a, b, p)]
    terbuka = [f"{g['nama']}" for g in snap.get("sg") or [] for r in g["masuk"]
               if "0.0.0.0/0" in r["cidr"] or "::/0" in r["cidr6"]]
    web_asing = [r for r in (sgs.get("web") or {}).get("masuk", []) if r["cidr"] or r["cidr6"]
                 or any(x != (sgs.get("alb") or {}).get("id") for x in r["sg"])]
    db_asing = [r for r in (sgs.get("db") or {}).get("masuk", []) if r["cidr"] or r["cidr6"]
                or any(x != (sgs.get("web") or {}).get("id") for x in r["sg"])]
    alb_asing = [r for r in (sgs.get("alb") or {}).get("masuk", [])
                 if r["dari"] != 80 or r["ke"] != 80 or r["sg"] or r["cidr6"]
                 or not all(c.endswith("/32") for c in r["cidr"])]
    neg_ok = bool(sgs) and not neg and not terbuka and not web_asing and not db_asing and not alb_asing
    neg_pesan = "semua jalur terlarang tertutup; tidak ada 0.0.0.0/0"
    if not neg_ok:
        neg_pesan = "; ".join(filter(None, [
            f"terbuka: {', '.join(neg)}" if neg else "",
            f"0.0.0.0/0 di {', '.join(sorted(set(terbuka)))}" if terbuka else "",
            "SG web menerima selain dari SG alb" if web_asing else "",
            "SG db menerima selain dari SG web" if db_asing else "",
            "SG alb harus hanya port 80 dari /32" if alb_asing else "",
        ])) or "security group peran belum lengkap"

    jaringan = vpcs + subs
    aplikasi = inst + [g for g in snap.get("sg") or [] if g["tags"].get("peran") in ("alb", "web", "db")]
    stack_ok = bool(jaringan) and bool(aplikasi) \
        and all(o["tags"].get("stack") == "m03-network" for o in jaringan) \
        and all(o["tags"].get("stack") == "m03-app" for o in aplikasi)
    milik = vpcs + subs + inst
    return [
        hasil("vpc_ada", vpc_ok, f"VPC m03: {[v['cidr'] for v in vpcs] or 'belum ada'} (harus tepat satu /16 di 10.0.0.0/8)"),
        hasil("subnet_publik_privat", subnet_ok,
              f"{len(publik)} subnet publik, {len(privat)} subnet privat di "
              f"{len({s['az'] for s in subs})} AZ; subnet privat tanpa IP publik otomatis"),
        hasil("rute_benar", rute_ok, "publik: 0.0.0.0/0 -> IGW; privat: tanpa rute keluar"),
        hasil("tanpa_nat", not snap.get("nat"), "tidak ada NAT Gateway" if not snap.get("nat")
              else f"NAT Gateway hidup (mahal, hapus): {', '.join(snap['nat'])}"),
        hasil("tiga_sg", {"alb", "web", "db"} <= set(sgs),
              f"SG berperan: {sorted(p for p in sgs if p != 'bawaan')}"),
        hasil("instance_privat", inst_ok, f"{len(web)} web dan {len(db)} db di subnet privat, tanpa IP publik, dengan SG perannya"),
        hasil("lb_sehat", lb_ok, f"ALB {lb['state'] if lb else 'belum ada'}, {len(sehat)} target healthy"),
        hasil("matriks_positif", bool(sgs) and not pos,
              "alb->web:80 dan web->db:5432 diizinkan" if not pos else f"tertutup: {', '.join(pos)}"),
        hasil("matriks_negatif", neg_ok, neg_pesan),
        hasil("stack_terpisah", stack_ok, "VPC/subnet stack=m03-network; instance/SG aplikasi stack=m03-app"),
        hasil("dikelola_kode", bool(milik) and all(o["tags"].get("managed-by") == "opentofu" for o in milik),
              "VPC, subnet, dan instance m03 bertag managed-by=opentofu"),
        hasil("tag_pemilik", bool(milik) and all(o["tags"].get("nim") == nim and o["tags"].get("kelompok") == kel
                                                 for o in milik), f"tag nim={nim} dan kelompok={kel}"),
        hasil("nama_konvensi", bool(milik) and all(o["tags"].get("Name", "").startswith(awalan) for o in milik)
              and (lb is None or lb["nama"].startswith(f"koma-{nim}-m03")),
              f"Name diawali {awalan}; ALB bernama koma-{nim}-m03"),
    ]


def periksa_selalu(snap: Mapping[str, Any], ident: Mapping[str, str]) -> list[dict[str, Any]]:
    liar = snap.get("liar") or []
    return [hasil("tanpa_instance_liar", not liar,
                  "tidak ada instance tanpa tag managed-by" if not liar
                  else "instance di luar kode masih hidup: " + ", ".join(i["id"] for i in liar))]


def periksa_riwayat(riwayat: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aktif = [p for p in riwayat if p.get("aktif") and p.get("vpc") and p.get("lb")]
    siklus = any(a["vpc"] == b["vpc"] and a["lb"] != b["lb"]
                 for i, a in enumerate(aktif) for b in aktif[i + 1:])
    pernah = any(p.get("aktif") for p in riwayat)
    akhir = riwayat[-1] if riwayat else {}
    bersih = pernah and not akhir.get("aktif") and not akhir.get("vpc")
    pesan = "potret terakhir: tanpa VPC, instance, dan ALB m03"
    if akhir.get("vpc") and not akhir.get("aktif"):
        pesan = "VPC m03 masih ada: destroy juga stack m03-network"
    return [
        hasil("siklus_terpisah", siklus, "stack app dibangun ulang (ALB baru) tanpa mengganti VPC"),
        hasil("bersih_akhir", bersih, pesan),
    ]
