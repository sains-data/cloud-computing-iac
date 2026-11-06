"""Pengumpul keadaan akun AWS untuk cek modul (lewat AwsCli, sehingga mudah dipalsukan di uji)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from .awsapi import GalatAws

STATE_HIDUP = ("pending", "running", "stopping", "stopped")
_SNAP_AMI = re.compile(r"CreateImage\([^)]*\) for (ami-[0-9a-f]+)")


def _tags(daftar: Any) -> dict[str, str]:
    return {t["Key"]: t["Value"] for t in daftar or [] if "Key" in t}


def identitas_akun(api) -> dict[str, str]:
    r = api.panggil("sts", "get-caller-identity", region=False)
    return {"akun": str(r.get("Account", "")), "arn": str(r.get("Arn", ""))}


def _instances(api, *filters: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-instances", "--filters",
                    f"Name=instance-state-name,Values={','.join(STATE_HIDUP)}", *filters)
    hasil = []
    for res in r.get("Reservations", []):
        for i in res.get("Instances", []):
            tags = _tags(i.get("Tags"))
            hasil.append({
                "id": i.get("InstanceId"),
                "nama": tags.get("Name", ""),
                "state": (i.get("State") or {}).get("Name"),
                "tipe": i.get("InstanceType"),
                "image": i.get("ImageId"),
                "ip_publik": i.get("PublicIpAddress"),
                "sg": [g.get("GroupId") for g in i.get("SecurityGroups", [])],
                "subnet": i.get("SubnetId"),
                "tags": tags,
            })
    return sorted(hasil, key=lambda x: (x["nama"], x["id"] or ""))


def instance_modul(api, nim: str, modul: str) -> list[dict[str, Any]]:
    return _instances(api, f"Name=tag:nim,Values={nim}", f"Name=tag:modul,Values={modul}")


def instance_liar(api) -> list[dict[str, Any]]:
    """Instance hidup tanpa tag managed-by (dibuat lewat konsol atau CLI, bukan kode)."""
    return [{"id": i["id"], "nama": i["nama"], "state": i["state"]}
            for i in _instances(api) if "managed-by" not in i["tags"]]


def images_modul(api, nim: str, modul: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-images", "--owners", "self", "--filters",
                    f"Name=tag:nim,Values={nim}", f"Name=tag:modul,Values={modul}",
                    "Name=state,Values=pending,available,failed")
    hasil = []
    for im in r.get("Images", []):
        # AMI yang baru dideregistrasi bisa sesaat masih tampil; bukan sisa milik modul.
        if im.get("State") in ("deregistered", "disabled"):
            continue
        hasil.append({
            "id": im.get("ImageId"),
            "nama": im.get("Name", ""),
            "state": im.get("State"),
            "tags": _tags(im.get("Tags")),
            "snapshots": sorted(b["Ebs"]["SnapshotId"] for b in im.get("BlockDeviceMappings", [])
                                if (b.get("Ebs") or {}).get("SnapshotId")),
        })
    return sorted(hasil, key=lambda x: x["nama"])


def snapshot_yatim(api) -> list[str]:
    """Snapshot hasil CreateImage yang AMI-nya sudah tidak ada (tetap ditagih bila dibiarkan)."""
    snaps = api.panggil("ec2", "describe-snapshots", "--owner-ids", "self").get("Snapshots", [])
    amis = {im.get("ImageId") for im in api.panggil("ec2", "describe-images", "--owners", "self").get("Images", [])}
    yatim = []
    for s in snaps:
        m = _SNAP_AMI.search(s.get("Description") or "")
        if m and m.group(1) not in amis:
            yatim.append(s.get("SnapshotId"))
    return sorted(yatim)


def anggaran(api, akun: str) -> list[dict[str, Any]]:
    try:
        r = api.panggil("budgets", "describe-budgets", "--account-id", akun, region=False)
    except GalatAws as exc:
        if "NotFound" in str(exc):
            return []
        raise
    hasil = []
    for b in r.get("Budgets", []):
        batas = (b.get("BudgetLimit") or {})
        try:
            jumlah = float(batas.get("Amount", "0"))
        except ValueError:
            jumlah = 0.0
        hasil.append({"nama": b.get("BudgetName"), "batas": jumlah, "unit": batas.get("Unit"),
                      "jenis": b.get("BudgetType")})
    return hasil


def security_groups(api, ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    r = api.panggil("ec2", "describe-security-groups", "--group-ids", *sorted(set(ids)))
    hasil = []
    for g in r.get("SecurityGroups", []):
        masuk = []
        for p in g.get("IpPermissions", []):
            masuk.append({
                "proto": p.get("IpProtocol"),
                "dari": p.get("FromPort"),
                "ke": p.get("ToPort"),
                "cidr": sorted(x.get("CidrIp") for x in p.get("IpRanges", [])),
                "cidr6": sorted(x.get("CidrIpv6") for x in p.get("Ipv6Ranges", [])),
                "sg": sorted(x.get("GroupId") for x in p.get("UserIdGroupPairs", [])),
            })
        hasil.append({"id": g.get("GroupId"), "nama": g.get("GroupName"), "vpc": g.get("VpcId"), "masuk": masuk,
                      "tags": _tags(g.get("Tags"))})
    return hasil


def http_get(url: str, timeout: float = 4.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (URL dari instance sendiri)
            data = r.read(65536).decode("utf-8", "replace")
            kode = r.status
    except urllib.error.HTTPError as exc:
        return {"kode": exc.code, "isi": None, "galat": None}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"kode": None, "isi": None, "galat": str(getattr(exc, "reason", exc))[:200]}
    try:
        isi: Any = json.loads(data)
    except ValueError:
        isi = data[:500]
    return {"kode": kode, "isi": isi, "galat": None}


def ip_publik(timeout: float = 5.0) -> str:
    with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=timeout) as r:
        return r.read().decode().strip()


def sisa(api) -> dict[str, Any]:
    r = api.panggil("resourcegroupstaggingapi", "get-resources", "--tag-filters",
                    "Key=kursus,Values=komputasi-awan")
    arn = sorted(x.get("ResourceARN") for x in r.get("ResourceTagMappingList", []))
    return {"bertag": arn, "liar": instance_liar(api), "snapshot_yatim": snapshot_yatim(api)}


# ----------------------------------------------------------------- jaringan (M03+)

def vpc_modul(api, nim: str, modul: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-vpcs", "--filters", f"Name=tag:nim,Values={nim}",
                    f"Name=tag:modul,Values={modul}")
    return sorted(({"id": v.get("VpcId"), "cidr": v.get("CidrBlock"), "state": v.get("State"),
                    "tags": _tags(v.get("Tags"))} for v in r.get("Vpcs", [])), key=lambda x: x["id"] or "")


def subnets(api, vpc_id: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-subnets", "--filters", f"Name=vpc-id,Values={vpc_id}")
    return sorted(({"id": s.get("SubnetId"), "az": s.get("AvailabilityZone"), "cidr": s.get("CidrBlock"),
                    "ip_publik_otomatis": bool(s.get("MapPublicIpOnLaunch")), "tags": _tags(s.get("Tags"))}
                   for s in r.get("Subnets", [])), key=lambda x: x["id"] or "")


def route_tables(api, vpc_id: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-route-tables", "--filters", f"Name=vpc-id,Values={vpc_id}")
    hasil = []
    for rt in r.get("RouteTables", []):
        asosiasi = rt.get("Associations", [])
        hasil.append({
            "id": rt.get("RouteTableId"),
            "utama": any(a.get("Main") for a in asosiasi),
            "subnets": sorted(a["SubnetId"] for a in asosiasi if a.get("SubnetId")),
            "rute": sorted(({"tujuan": x.get("DestinationCidrBlock") or x.get("DestinationIpv6CidrBlock")
                             or x.get("DestinationPrefixListId"),
                             "lewat": x.get("GatewayId") or x.get("NatGatewayId") or x.get("TransitGatewayId")
                             or x.get("NetworkInterfaceId") or x.get("VpcPeeringConnectionId") or x.get("InstanceId")}
                            for x in rt.get("Routes", [])), key=lambda x: str(x["tujuan"])),
            "tags": _tags(rt.get("Tags")),
        })
    return sorted(hasil, key=lambda x: x["id"] or "")


def nat_hidup(api) -> list[str]:
    r = api.panggil("ec2", "describe-nat-gateways", "--filter", "Name=state,Values=pending,available")
    return sorted(n.get("NatGatewayId") for n in r.get("NatGateways", []))


def sg_vpc(api, vpc_id: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-security-groups", "--filters", f"Name=vpc-id,Values={vpc_id}")
    ids = [g.get("GroupId") for g in r.get("SecurityGroups", [])]
    return security_groups(api, ids) if ids else []


def load_balancers(api, vpc_id: str) -> list[dict[str, Any]]:
    r = api.panggil("elbv2", "describe-load-balancers")
    hasil = []
    for lb in r.get("LoadBalancers", []):
        if lb.get("VpcId") != vpc_id:
            continue
        arn = lb.get("LoadBalancerArn")
        tgs = api.panggil("elbv2", "describe-target-groups", "--load-balancer-arn", arn).get("TargetGroups", [])
        grup = []
        for tg in tgs:
            th = api.panggil("elbv2", "describe-target-health", "--target-group-arn", tg["TargetGroupArn"])
            grup.append({"arn": tg["TargetGroupArn"], "nama": tg.get("TargetGroupName"), "port": tg.get("Port"),
                         "target": sorted(({"id": t["Target"]["Id"], "state": (t.get("TargetHealth") or {}).get("State")}
                                           for t in th.get("TargetHealthDescriptions", [])), key=lambda x: x["id"])})
        hasil.append({
            "arn": arn, "nama": lb.get("LoadBalancerName"), "dns": lb.get("DNSName"),
            "state": (lb.get("State") or {}).get("Code"), "skema": lb.get("Scheme"), "tipe": lb.get("Type"),
            "azs": sorted(z.get("ZoneName") for z in lb.get("AvailabilityZones", [])),
            "subnets": sorted(z.get("SubnetId") for z in lb.get("AvailabilityZones", [])),
            "sg": sorted(lb.get("SecurityGroups", [])), "target_groups": grup,
        })
    return sorted(hasil, key=lambda x: x["nama"] or "")


# ----------------------------------------------------------------- storage (M04+)

def volumes_modul(api, nim: str, modul: str) -> list[dict[str, Any]]:
    r = api.panggil("ec2", "describe-volumes", "--filters", f"Name=tag:nim,Values={nim}",
                    f"Name=tag:modul,Values={modul}")
    hasil = []
    for v in r.get("Volumes", []):
        hasil.append({
            "id": v.get("VolumeId"), "az": v.get("AvailabilityZone"), "ukuran": v.get("Size"),
            "tipe": v.get("VolumeType"), "terenkripsi": bool(v.get("Encrypted")), "state": v.get("State"),
            "pasang": [{"instance": a.get("InstanceId"), "state": a.get("State"),
                        "hapus_bersama": bool(a.get("DeleteOnTermination"))} for a in v.get("Attachments", [])],
            "tags": _tags(v.get("Tags")),
        })
    return sorted(hasil, key=lambda x: x["id"] or "")


def _s3_opsional(api, *args: str) -> Any:
    """Panggilan s3api yang wajar gagal bila konfigurasinya belum ada (NoSuch...)."""
    try:
        return api.panggil("s3api", *args)
    except GalatAws as exc:
        if "NoSuch" in str(exc) or "NotFound" in str(exc) or "ServerSideEncryptionConfigurationNotFound" in str(exc):
            return None
        raise


def bucket_saya(api, awalan: str, prefix_objek: str | None = None) -> list[dict[str, Any]]:
    """Bucket bernama awalan* beserta konfigurasi pentingnya (tanpa membaca isi objek)."""
    r = api.panggil("s3api", "list-buckets", region=False)
    hasil = []
    for b in r.get("Buckets", []):
        nama = b.get("Name", "")
        if not nama.startswith(awalan):
            continue
        ver = _s3_opsional(api, "get-bucket-versioning", "--bucket", nama) or {}
        pab = (_s3_opsional(api, "get-public-access-block", "--bucket", nama) or {}).get(
            "PublicAccessBlockConfiguration") or {}
        enk = (_s3_opsional(api, "get-bucket-encryption", "--bucket", nama) or {}).get(
            "ServerSideEncryptionConfiguration") or {}
        lc = (_s3_opsional(api, "get-bucket-lifecycle-configuration", "--bucket", nama) or {}).get("Rules") or []
        tag = _tags((_s3_opsional(api, "get-bucket-tagging", "--bucket", nama) or {}).get("TagSet"))
        objek: dict[str, int] = {}
        if prefix_objek is not None:
            ov = _s3_opsional(api, "list-object-versions", "--bucket", nama, "--prefix", prefix_objek) or {}
            for v in ov.get("Versions", []):
                objek[v["Key"]] = objek.get(v["Key"], 0) + 1
        hasil.append({
            "nama": nama, "versioning": ver.get("Status"),
            "publik_diblok": bool(pab) and all(pab.get(k) for k in ("BlockPublicAcls", "IgnorePublicAcls",
                                                                    "BlockPublicPolicy", "RestrictPublicBuckets")),
            "enkripsi": [r2.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm") for r2 in enk.get("Rules", [])],
            "lifecycle": [{"id": x.get("ID"), "status": x.get("Status"),
                           "versi_lama": "NoncurrentVersionExpiration" in x,
                           "kedaluwarsa": "Expiration" in x, "transisi": bool(x.get("Transitions"))} for x in lc],
            "tags": tag, "versi_objek": objek,
        })
    return sorted(hasil, key=lambda x: x["nama"])


def penanda_konsol(api, instance_id: str) -> list[str]:
    """Baris KOMA-PENANDA dari log konsol server (dibaca dari laptop mahasiswa)."""
    try:
        r = api.panggil("ec2", "get-console-output", "--instance-id", instance_id, "--latest")
    except GalatAws:
        return []
    return [b.strip() for b in str(r.get("Output") or "").splitlines() if "KOMA-PENANDA" in b][-3:]
