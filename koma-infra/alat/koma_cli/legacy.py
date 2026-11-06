"""Sistem legacy Modul 06: server dan security group yang dibuat lewat AWS CLI, bukan kode.

`koma legacy buat` meniru kontraktor yang membangun server dengan tangan: tidak ada state, tidak
ada tag `managed-by`. Mahasiswa kemudian mengimpornya ke OpenTofu (Bagian B). Nama, deskripsi,
dan aturan di sini HARUS sama dengan `stacks/m06-migrasi/legacy.tf`, karena perbedaan sekecil apa
pun membuat impor berubah menjadi penggantian.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
from typing import Any, Mapping

from .awsapi import GalatAws

VERSI_LEGACY = "0.9.0"
DESKRIPSI_SG = "Web lama koma-api (dibuat manual)"
DESKRIPSI_ATURAN = "HTTP dari kantor"
PARAM_AMI = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"


def nama(ident: Mapping[str, str]) -> str:
    return f"koma-{ident['nim']}-m06-legacy"


def tag(ident: Mapping[str, str], server: bool = True) -> list[dict[str, str]]:
    # Tag yang dipasang kontraktor: cukup untuk menemukan servernya, tanpa managed-by dan stack.
    # `versi` hanya pada server, sama dengan legacy.tf, sehingga impor hanya MENAMBAH tag.
    pasangan = [("Name", nama(ident)), ("peran", "legacy")] + ([("versi", VERSI_LEGACY)] if server else []) + [
        ("nim", ident["nim"]), ("kelompok", ident["kelompok"]), ("modul", "m06"), ("kursus", "komputasi-awan")]
    return [{"Key": k, "Value": v} for k, v in pasangan]


def user_data(aplikasi: bytes) -> str:
    gz = base64.b64encode(gzip.compress(aplikasi, mtime=0)).decode()
    return f"""#cloud-config
write_files:
  - path: /opt/koma/koma_api.py
    permissions: "0755"
    encoding: gz+b64
    content: {gz}
  - path: /etc/systemd/system/koma-api.service
    permissions: "0644"
    content: |
      [Unit]
      Description=koma-api {VERSI_LEGACY} (legacy)
      After=network-online.target

      [Service]
      Environment=KOMA_VERSI={VERSI_LEGACY}
      Environment=KOMA_PERAN=legacy
      ExecStart=/usr/bin/python3 /opt/koma/koma_api.py --port 80
      DynamicUser=yes
      AmbientCapabilities=CAP_NET_BIND_SERVICE
      Restart=always

      [Install]
      WantedBy=multi-user.target
runcmd:
  - systemctl daemon-reload
  - systemctl enable --now koma-api.service
"""


def _spesifikasi_tag(jenis: str, ident) -> str:
    return json.dumps([{"ResourceType": jenis, "Tags": tag(ident, server=jenis == "instance")}])


def cari(api, ident: Mapping[str, str]) -> dict[str, Any]:
    """Server, SG, dan aturan legacy yang ada (dicari dari nama dan tag, bukan dari berkas lokal)."""
    sg = api.panggil("ec2", "describe-security-groups", "--filters", f"Name=group-name,Values={nama(ident)}")
    grup = (sg.get("SecurityGroups") or [None])[0]
    aturan = None
    if grup:
        r = api.panggil("ec2", "describe-security-group-rules", "--filters", f"Name=group-id,Values={grup['GroupId']}")
        aturan = next((x for x in r.get("SecurityGroupRules", [])
                       if not x.get("IsEgress") and x.get("FromPort") == 80 and x.get("CidrIpv4")), None)
    ins = api.panggil("ec2", "describe-instances", "--filters", f"Name=tag:Name,Values={nama(ident)}",
                      "Name=instance-state-name,Values=pending,running,stopping,stopped")
    server = next((i for res in ins.get("Reservations", []) for i in res.get("Instances", [])), None)
    tags = {t["Key"]: t["Value"] for t in (server or {}).get("Tags", [])}
    return {
        "sg": grup["GroupId"] if grup else None,
        "aturan": aturan["SecurityGroupRuleId"] if aturan else None,
        "cidr": aturan.get("CidrIpv4") if aturan else None,
        "instance": server["InstanceId"] if server else None,
        "ip": (server or {}).get("PublicIpAddress"),
        "state": ((server or {}).get("State") or {}).get("Name"),
        "dikelola": tags.get("managed-by") == "opentofu",
    }


def buat(api, ident: Mapping[str, str], cidr: str, aplikasi: bytes) -> dict[str, Any]:
    ada = cari(api, ident)
    if ada["instance"] or ada["sg"]:
        raise GalatAws(f"legacy sudah ada (instance {ada['instance']}, SG {ada['sg']}); pakai `koma legacy info`")
    vpc = api.panggil("ec2", "describe-vpcs", "--filters", "Name=isDefault,Values=true").get("Vpcs", [])
    if not vpc:
        raise GalatAws("VPC bawaan tidak ditemukan di region ini")
    ami = api.panggil("ssm", "get-parameters", "--names", PARAM_AMI)["Parameters"][0]["Value"]
    sg = api.panggil("ec2", "create-security-group", "--group-name", nama(ident), "--description", DESKRIPSI_SG,
                     "--vpc-id", vpc[0]["VpcId"], "--tag-specifications",
                     _spesifikasi_tag("security-group", ident))["GroupId"]
    izin = json.dumps([{"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                        "IpRanges": [{"CidrIp": cidr, "Description": DESKRIPSI_ATURAN}]}])
    api.panggil("ec2", "authorize-security-group-ingress", "--group-id", sg, "--ip-permissions", izin)
    api.panggil("ec2", "run-instances", "--image-id", ami, "--instance-type", "t3.micro", "--count", "1",
                "--security-group-ids", sg, "--user-data", user_data(aplikasi),
                "--tag-specifications", _spesifikasi_tag("instance", ident))
    return cari(api, ident)


def hapus(api, ident: Mapping[str, str]) -> dict[str, Any]:
    """Jalur darurat sebelum impor. Server yang sudah dikelola OpenTofu tidak disentuh."""
    ada = cari(api, ident)
    if ada["dikelola"]:
        raise GalatAws("legacy sudah diimpor ke OpenTofu; bongkar lewat kode (pertahankan_legacy = false)")
    if ada["instance"]:
        api.panggil("ec2", "terminate-instances", "--instance-ids", ada["instance"])
        api.panggil("ec2", "wait", "instance-terminated", "--instance-ids", ada["instance"])
    if ada["sg"]:
        api.panggil("ec2", "delete-security-group", "--group-id", ada["sg"])
    return ada


def baca_aplikasi(akar: Path) -> bytes:
    p = akar / "app" / "koma_api.py"
    if not p.is_file():
        raise GalatAws(f"{p} tidak ada; jalankan `koma ambil` starter Modul 06 dulu")
    return p.read_bytes()
