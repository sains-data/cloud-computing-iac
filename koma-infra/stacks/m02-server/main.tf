# Modul 02 — server sebagai kode: panggang (bake) AMI lalu sajikan (serve).
# Ikuti naskah Bagian B (panggang) dan C (sajikan).

locals {
  awalan = "koma-${var.nim}-m02"
  cloud_init = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    versi       = var.versi
    aplikasi_gz = base64gzip(file("${path.module}/../../app/koma_api.py"))
  })
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

data "aws_vpc" "bawaan" {
  default = true
}

# TODO B.1  aws_instance.pembangun  : AMI publik + user_data = local.cloud_init,
#           user_data_replace_on_change = true, tanpa IP publik, tag peran/versi
# TODO B.2  time_sleep.tunggu_cloud_init : jeda var.tunggu_cloud_init, triggers = id pembangun
# TODO B.3  aws_ami_from_instance.api : nama "${local.awalan}-api-${var.versi}"

# TODO C.1  aws_security_group.api + aws_vpc_security_group_ingress_rule.http_saya
#           (port 80 hanya dari var.cidr_saya)
# TODO C.2  aws_instance.api : dari AMI sendiri, IP publik, SG api, tag peran/versi

# Latihan 2.1: aws_instance.goreng (count = var.bandingkan_goreng ? 1 : 0)
