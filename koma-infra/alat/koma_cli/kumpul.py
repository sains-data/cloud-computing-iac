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
                "imds": (i.get("MetadataOptions") or {}).get("HttpTokens"),
                "profil": (i.get("IamInstanceProfile") or {}).get("Arn"),
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
                      "jenis": b.get("BudgetType"), "saringan": b.get("CostFilters") or {}})
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


def _kunci_menunggu_hapus(api, arn: str) -> bool:
    try:
        meta = api.panggil("kms", "describe-key", "--key-id", arn).get("KeyMetadata") or {}
    except GalatAws:
        return False
    return meta.get("KeyState") == "PendingDeletion"


def sisa(api) -> dict[str, Any]:
    r = api.panggil("resourcegroupstaggingapi", "get-resources", "--tag-filters",
                    "Key=kursus,Values=komputasi-awan")
    arn = sorted(x.get("ResourceARN") for x in r.get("ResourceTagMappingList", []))
    # Kunci KMS yang sudah di-destroy menunggu 7-30 hari sebelum benar-benar hilang (tidak ditagih).
    menunggu = [a for a in arn if ":kms:" in a and ":key/" in a and _kunci_menunggu_hapus(api, a)]
    return {"bertag": [a for a in arn if a not in menunggu], "kunci_menunggu": menunggu,
            "liar": instance_liar(api), "snapshot_yatim": snapshot_yatim(api)}


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


# ----------------------------------------------------------------- keamanan (M05+)

#: nilai rahasia tertulis langsung (NAMA=nilai), bukan rujukan (NAMA=$VARIABEL); sama dengan Rego aturan 5
POLA_NILAI_RAHASIA = re.compile(r"(?i)(password|passwd|secret|token)\s*[=:]\s*[\"']?[^\s\"'$]")


def sumber_bertag(api, nim: str, modul: str) -> list[dict[str, Any]]:
    """Semua resource bertag nim + modul (Resource Groups Tagging API), beserta tag-nya."""
    r = api.panggil("resourcegroupstaggingapi", "get-resources", "--tag-filters",
                    f"Key=nim,Values={nim}", f"Key=modul,Values={modul}")
    return sorted(({"arn": x.get("ResourceARN"), "tags": _tags(x.get("Tags"))}
                   for x in r.get("ResourceTagMappingList", [])), key=lambda x: x["arn"] or "")


def user_data_rahasia(api, instance_id: str) -> dict[str, bool]:
    """Apakah user data instance memuat nilai rahasia. Isinya tidak pernah dikembalikan."""
    import base64
    r = api.panggil("ec2", "describe-instance-attribute", "--instance-id", instance_id, "--attribute", "userData")
    mentah = ((r.get("UserData") or {}).get("Value")) or ""
    try:
        teks = base64.b64decode(mentah).decode("utf-8", "replace")
    except ValueError:
        teks = ""
    return {"ada": bool(teks), "rahasia": bool(POLA_NILAI_RAHASIA.search(teks)) or "koma123" in teks}


def blok_publik_akun(api, akun: str) -> dict[str, bool] | None:
    try:
        r = api.panggil("s3control", "get-public-access-block", "--account-id", akun)
    except GalatAws as exc:
        if "NoSuchPublicAccessBlockConfiguration" in str(exc):
            return None
        raise
    c = r.get("PublicAccessBlockConfiguration") or {}
    return {k: bool(c.get(k)) for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy",
                                        "RestrictPublicBuckets")}


def kebijakan_bucket_publik(api, nama: str) -> bool | None:
    """IsPublic menurut S3; None bila bucket tidak punya kebijakan."""
    r = _s3_opsional(api, "get-bucket-policy-status", "--bucket", nama)
    return None if r is None else bool((r.get("PolicyStatus") or {}).get("IsPublic"))


def parameter_awalan(api, awalan: str) -> list[dict[str, Any]]:
    """Metadata parameter SSM (tanpa nilai)."""
    r = api.panggil("ssm", "describe-parameters", "--parameter-filters",
                    f"Key=Name,Option=BeginsWith,Values={awalan}")
    return sorted(({"nama": p.get("Name"), "tipe": p.get("Type"), "kunci": p.get("KeyId"),
                    "versi": p.get("Version")} for p in r.get("Parameters", [])), key=lambda x: x["nama"] or "")


def kunci_kms(api, arn: str) -> dict[str, Any]:
    meta = api.panggil("kms", "describe-key", "--key-id", arn).get("KeyMetadata") or {}
    rotasi = None
    if meta.get("KeyState") == "Enabled":
        rotasi = bool(api.panggil("kms", "get-key-rotation-status", "--key-id", arn).get("KeyRotationEnabled"))
    return {"arn": meta.get("Arn") or arn, "id": meta.get("KeyId"), "state": meta.get("KeyState"),
            "pengelola": meta.get("KeyManager"), "rotasi": rotasi}


def _dokumen(d: Any) -> dict[str, Any]:
    if isinstance(d, str):
        from urllib.parse import unquote
        return json.loads(unquote(d))
    return d or {}


def profil_iam(api, profil_arn: str) -> dict[str, Any] | None:
    """Kebijakan role di balik instance profile: pernyataan inline dan kebijakan terlampir."""
    nama = profil_arn.rsplit("/", 1)[-1]
    try:
        prof = api.panggil("iam", "get-instance-profile", "--instance-profile-name", nama).get("InstanceProfile") or {}
    except GalatAws as exc:
        if "NoSuchEntity" in str(exc):
            return None
        raise
    peran = []
    for role in prof.get("Roles", []):
        rn = role.get("RoleName")
        inline = []
        for pn in api.panggil("iam", "list-role-policies", "--role-name", rn).get("PolicyNames", []):
            doc = _dokumen(api.panggil("iam", "get-role-policy", "--role-name", rn, "--policy-name", pn).get("PolicyDocument"))
            st = doc.get("Statement", [])
            for s in ([st] if isinstance(st, dict) else st):
                aksi = s.get("Action", [])
                res = s.get("Resource", [])
                inline.append({"kebijakan": pn, "efek": s.get("Effect"),
                               "aksi": [aksi] if isinstance(aksi, str) else list(aksi),
                               "resource": [res] if isinstance(res, str) else list(res)})
        terlampir = [p.get("PolicyArn") for p in
                     api.panggil("iam", "list-attached-role-policies", "--role-name", rn).get("AttachedPolicies", [])]
        peran.append({"nama": rn, "inline": inline, "terlampir": sorted(terlampir)})
    return {"nama": nama, "peran": peran}


def awal_objek(api, bucket: str, key: str, n: int = 100) -> bytes | None:
    """n byte pertama objek (permintaan Range), atau None bila objek tidak ada."""
    try:
        return api.baca_awal(bucket, key, n)
    except GalatAws as exc:
        if "NoSuchKey" in str(exc) or "Not Found" in str(exc) or "404" in str(exc):
            return None
        raise


def format_state(awal: bytes | None) -> str:
    """'terenkripsi', 'teks' (state biasa), 'tidak-ada', atau 'tidak-dikenal' dari awal berkas state."""
    if awal is None:
        return "tidak-ada"
    t = awal.decode("utf-8", "replace")
    if '"terraform_version"' in t or re.search(r'^\s*\{\s*"version"', t):
        return "teks"
    if '"meta"' in t or '"encrypted_data"' in t:
        return "terenkripsi"
    return "tidak-dikenal"


# ----------------------------------------------------------------- migrasi dan observability (M06+)

def alb_bernama(api, nama: str, awalan_tg: str) -> dict[str, Any] | None:
    """ALB bernama tepat `nama`, listener port 80, dan target group berawalan `awalan_tg`."""
    try:
        lbs = api.panggil("elbv2", "describe-load-balancers", "--names", nama).get("LoadBalancers", [])
    except GalatAws as exc:
        if "LoadBalancerNotFound" in str(exc) or "not found" in str(exc).lower():
            return None
        raise
    if not lbs:
        return None
    lb = lbs[0]
    arn = lb.get("LoadBalancerArn")
    tujuan, bobot = None, {}
    for ls in api.panggil("elbv2", "describe-listeners", "--load-balancer-arn", arn).get("Listeners", []):
        if ls.get("Port") == 80:
            for act in ls.get("DefaultActions", []):
                if act.get("Type") == "forward":
                    daftar = (act.get("ForwardConfig") or {}).get("TargetGroups", [])
                    tujuan = act.get("TargetGroupArn") or next((t.get("TargetGroupArn") for t in daftar), None)
                    bobot = {t.get("TargetGroupArn"): int(t.get("Weight", 1)) for t in daftar}
                    if not bobot and act.get("TargetGroupArn"):
                        bobot = {act["TargetGroupArn"]: 1}
    grup = {}
    for tg in api.panggil("elbv2", "describe-target-groups").get("TargetGroups", []):
        if not str(tg.get("TargetGroupName", "")).startswith(awalan_tg):
            continue
        th = api.panggil("elbv2", "describe-target-health", "--target-group-arn", tg["TargetGroupArn"])
        grup[tg["TargetGroupName"]] = {
            "arn": tg["TargetGroupArn"],
            "target": sorted(({"id": t["Target"]["Id"], "state": (t.get("TargetHealth") or {}).get("State")}
                              for t in th.get("TargetHealthDescriptions", [])), key=lambda x: x["id"]),
        }
    return {"arn": arn, "nama": lb.get("LoadBalancerName"), "dns": lb.get("DNSName"),
            "state": (lb.get("State") or {}).get("Code"), "akhiran": arn.split(":loadbalancer/", 1)[-1],
            "tujuan": tujuan, "bobot": bobot, "target_groups": grup}


def alarm_awalan(api, awalan: str) -> list[dict[str, Any]]:
    r = api.panggil("cloudwatch", "describe-alarms", "--alarm-name-prefix", awalan)
    hasil = []
    for a in r.get("MetricAlarms", []):
        nama = a.get("AlarmName")
        hist = api.panggil("cloudwatch", "describe-alarm-history", "--alarm-name", nama,
                           "--history-item-type", "StateUpdate").get("AlarmHistoryItems", [])
        pernah = a.get("StateValue") == "ALARM"
        for h in hist:
            try:
                data = json.loads(h.get("HistoryData") or "{}")
            except ValueError:
                data = {}
            if ((data.get("newState") or {}).get("stateValue")) == "ALARM":
                pernah = True
        hasil.append({"nama": nama, "state": a.get("StateValue"), "namespace": a.get("Namespace"),
                      "metrik": a.get("MetricName"), "statistik": a.get("ExtendedStatistic") or a.get("Statistic"),
                      "ambang": a.get("Threshold"),
                      "dimensi": {d.get("Name"): d.get("Value") for d in a.get("Dimensions", [])},
                      "pernah_alarm": pernah})
    return sorted(hasil, key=lambda x: x["nama"] or "")


def dasbor_awalan(api, awalan: str) -> list[str]:
    r = api.panggil("cloudwatch", "list-dashboards", "--dashboard-name-prefix", awalan)
    return sorted(d.get("DashboardName") for d in r.get("DashboardEntries", []))


def log_group_awalan(api, awalan: str) -> list[dict[str, Any]]:
    r = api.panggil("logs", "describe-log-groups", "--log-group-name-prefix", awalan)
    hasil = []
    for g in r.get("logGroups", []):
        nama = g.get("logGroupName")
        st = api.panggil("logs", "describe-log-streams", "--log-group-name", nama, "--order-by", "LastEventTime",
                         "--descending").get("logStreams", [])
        terakhir = max((s.get("lastEventTimestamp") or 0 for s in st), default=0)
        hasil.append({"nama": nama, "stream": len(st), "event_terakhir": terakhir or None,
                      "retensi": g.get("retentionInDays")})
    return sorted(hasil, key=lambda x: x["nama"] or "")


# ---------------------------------------------------------------------------- Modul 07

def topik_awalan(api, awalan: str) -> list[dict[str, Any]]:
    """Topik SNS bernama awalan* beserta langganannya (protokol, endpoint, raw)."""
    hasil = []
    for t in api.panggil("sns", "list-topics").get("Topics", []):
        arn = t.get("TopicArn") or ""
        nama = arn.rsplit(":", 1)[-1]
        if not nama.startswith(awalan):
            continue
        langganan = []
        for s in api.panggil("sns", "list-subscriptions-by-topic", "--topic-arn", arn).get("Subscriptions", []):
            sarn = s.get("SubscriptionArn") or ""
            raw = False
            if sarn.startswith("arn:"):
                atr = api.panggil("sns", "get-subscription-attributes", "--subscription-arn", sarn).get("Attributes") or {}
                raw = str(atr.get("RawMessageDelivery", "false")).lower() == "true"
            langganan.append({"protokol": s.get("Protocol"), "endpoint": s.get("Endpoint"), "raw": raw,
                              "terkonfirmasi": sarn.startswith("arn:")})
        hasil.append({"nama": nama, "arn": arn, "langganan": langganan})
    return sorted(hasil, key=lambda x: x["nama"])


def antrean_awalan(api, awalan: str) -> list[dict[str, Any]]:
    """Antrean SQS bernama awalan*: ARN, tujuan redrive (DLQ), dan perkiraan jumlah pesan."""
    hasil = []
    for url in api.panggil("sqs", "list-queues", "--queue-name-prefix", awalan).get("QueueUrls", []) or []:
        atr = api.panggil("sqs", "get-queue-attributes", "--queue-url", url,
                          "--attribute-names", "All").get("Attributes") or {}
        try:
            redrive = json.loads(atr.get("RedrivePolicy") or "{}")
        except ValueError:
            redrive = {}
        hasil.append({"nama": url.rsplit("/", 1)[-1], "url": url, "arn": atr.get("QueueArn"),
                      "redrive_ke": redrive.get("deadLetterTargetArn"),
                      "maks_terima": redrive.get("maxReceiveCount"),
                      "pesan": int(atr.get("ApproximateNumberOfMessages") or 0)
                      + int(atr.get("ApproximateNumberOfMessagesNotVisible") or 0)})
    return sorted(hasil, key=lambda x: x["nama"])


def fungsi_awalan(api, awalan: str) -> list[dict[str, Any]]:
    """Fungsi Lambda bernama awalan* beserta event source mapping-nya."""
    hasil = []
    for f in api.panggil("lambda", "list-functions").get("Functions", []):
        nama = f.get("FunctionName") or ""
        if not nama.startswith(awalan):
            continue
        pemetaan = [{"sumber": m.get("EventSourceArn"), "fungsi": m.get("FunctionArn"), "state": m.get("State")}
                    for m in api.panggil("lambda", "list-event-source-mappings", "--function-name", nama)
                    .get("EventSourceMappings", [])]
        hasil.append({"nama": nama, "arn": f.get("FunctionArn"), "memori": f.get("MemorySize"),
                      "timeout": f.get("Timeout"), "runtime": f.get("Runtime"), "pemetaan": pemetaan})
    return sorted(hasil, key=lambda x: x["nama"])


def oidc_github(api) -> dict[str, Any] | None:
    for p in api.panggil("iam", "list-open-id-connect-providers").get("OpenIDConnectProviderList", []):
        arn = p.get("Arn") or ""
        if arn.endswith("/token.actions.githubusercontent.com"):
            d = api.panggil("iam", "get-open-id-connect-provider", "--open-id-connect-provider-arn", arn)
            return {"arn": arn, "url": d.get("Url"), "audiens": sorted(d.get("ClientIDList") or [])}
    return None


def role_trust(api, nama: str) -> dict[str, Any] | None:
    """Kebijakan kepercayaan (trust policy) sebuah role, atau None bila role tidak ada."""
    try:
        r = api.panggil("iam", "get-role", "--role-name", nama).get("Role") or {}
    except GalatAws as exc:
        if "NoSuchEntity" in str(exc):
            return None
        raise
    return {"nama": r.get("RoleName"), "arn": r.get("Arn"), "trust": _dokumen(r.get("AssumeRolePolicyDocument")),
            "sesi_maks": r.get("MaxSessionDuration")}


def jejak_pipeline(api, nim: str, sesi_awalan: str = "koma-pipeline-", hari: int = 30, modul: str = "m07",
                   sumber_acara: tuple[str, ...] = ("lambda.amazonaws.com", "sns.amazonaws.com",
                                                    "sqs.amazonaws.com")) -> dict[str, Any]:
    """Ringkasan kejadian CloudTrail (manajemen) atas resource koma-<nim>-<modul>-* oleh role pipeline.

    Hanya nama kejadian dan waktunya yang disimpan; isi permintaan dibaca lalu dibuang.
    """
    import datetime as _dt

    mulai = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=hari)).strftime("%Y-%m-%dT%H:%M:%SZ")
    role = f"assumed-role/koma-{nim}-pipeline/"
    target = f"koma-{nim}-{modul}-"
    acara, terakhir = set(), None
    for sumber in sumber_acara:
        r = api.panggil("cloudtrail", "lookup-events", "--lookup-attributes",
                        f"AttributeKey=EventSource,AttributeValue={sumber}", "--start-time", mulai)
        for e in r.get("Events", []):
            if not str(e.get("Username") or "").startswith(sesi_awalan):
                continue
            try:
                ct = json.loads(e.get("CloudTrailEvent") or "{}")
            except ValueError:
                ct = {}
            if role not in str((ct.get("userIdentity") or {}).get("arn") or ""):
                continue
            if ct.get("readOnly") is True or target not in json.dumps(ct.get("requestParameters") or {}) + \
                    json.dumps(e.get("Resources") or []):
                continue
            acara.add(e.get("EventName"))
            waktu = str(e.get("EventTime"))
            terakhir = max(terakhir or waktu, waktu)
    return {"jumlah": len(acara), "acara": sorted(acara), "terakhir": terakhir}


# ---------------------------------------------------------------------------- Modul 08

def registri(api, nama: str) -> dict[str, Any] | None:
    """Repo ECR bernama tepat `nama` beserta tag image-nya (tanpa membaca isi image)."""
    try:
        repo = (api.panggil("ecr", "describe-repositories", "--repository-names", nama).get("repositories") or [None])[0]
    except GalatAws as exc:
        if "RepositoryNotFound" in str(exc):
            return None
        raise
    if not repo:
        return None
    gambar = api.panggil("ecr", "describe-images", "--repository-name", nama).get("imageDetails", [])
    return {"nama": repo.get("repositoryName"), "uri": repo.get("repositoryUri"),
            "mutabilitas": repo.get("imageTagMutability"),
            "pindai": bool((repo.get("imageScanningConfiguration") or {}).get("scanOnPush")),
            "tag": sorted({tg for g in gambar for tg in (g.get("imageTags") or [])})}


def layanan_ecs(api, cluster: str) -> dict[str, Any] | None:
    """Cluster ECS bernama `cluster`, layanannya, image task-nya, dan aturan skalanya."""
    cl = (api.panggil("ecs", "describe-clusters", "--clusters", cluster).get("clusters") or [])
    cl = next((c for c in cl if c.get("status") == "ACTIVE"), None)
    if not cl:
        return None
    arns = api.panggil("ecs", "list-services", "--cluster", cluster).get("serviceArns", []) or []
    layanan = []
    if arns:
        for s in api.panggil("ecs", "describe-services", "--cluster", cluster, "--services", *arns).get("services", []):
            if s.get("status") != "ACTIVE":
                continue
            td = api.panggil("ecs", "describe-task-definition", "--task-definition", s.get("taskDefinition")) \
                .get("taskDefinition") or {}
            wadah = (td.get("containerDefinitions") or [{}])[0]
            nama = s.get("serviceName")
            rid = f"service/{cluster}/{nama}"
            target = (api.panggil("application-autoscaling", "describe-scalable-targets", "--service-namespace", "ecs",
                                  "--resource-ids", rid).get("ScalableTargets") or [None])[0]
            kebijakan = api.panggil("application-autoscaling", "describe-scaling-policies", "--service-namespace", "ecs",
                                    "--resource-id", rid).get("ScalingPolicies", [])
            layanan.append({
                "nama": nama, "arn": s.get("serviceArn"), "jenis": s.get("launchType"),
                "diinginkan": s.get("desiredCount"), "berjalan": s.get("runningCount"),
                "image": wadah.get("image"),
                "target_group": [lb.get("targetGroupArn") for lb in s.get("loadBalancers", [])],
                "skala": {"min": target.get("MinCapacity"), "maks": target.get("MaxCapacity")} if target else None,
                "kebijakan": [((p.get("TargetTrackingScalingPolicyConfiguration") or {})
                               .get("PredefinedMetricSpecification") or {}).get("PredefinedMetricType")
                              for p in kebijakan if p.get("PolicyType") == "TargetTrackingScaling"],
            })
    return {"nama": cl.get("clusterName"), "arn": cl.get("clusterArn"), "layanan": sorted(layanan, key=lambda x: x["nama"])}
