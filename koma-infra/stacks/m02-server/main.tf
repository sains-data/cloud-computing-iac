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
resource "aws_instance" "pembangun" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = "t3.micro"
  associate_public_ip_address = false
  user_data                   = local.cloud_init
  user_data_replace_on_change = true

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name  = "${local.awalan}-pembangun"
    peran = "pembangun"
    versi = var.versi
  }
}
# TODO B.2  time_sleep.tunggu_cloud_init : jeda var.tunggu_cloud_init, triggers = id pembangun
# Instance "running" belum berarti cloud-init selesai; beri jeda sebelum memotret disk.
resource "time_sleep" "tunggu_cloud_init" {
  create_duration = var.tunggu_cloud_init
  triggers = {
    instance = aws_instance.pembangun.id
  }
}

# TODO B.3  aws_ami_from_instance.api : nama "${local.awalan}-api-${var.versi}"
resource "aws_ami_from_instance" "api" {
  name               = "${local.awalan}-api-${var.versi}"
  source_instance_id = time_sleep.tunggu_cloud_init.triggers["instance"]

  tags = {
    Name  = "${local.awalan}-api-${var.versi}"
    peran = "api"
    versi = var.versi
  }
}

# TODO C.1  aws_security_group.api + aws_vpc_security_group_ingress_rule.http_saya
#           (port 80 hanya dari var.cidr_saya)
resource "aws_security_group" "api" {
  name        = "${local.awalan}-api"
  description = "HTTP koma-api hanya dari komputer praktikan"
  vpc_id      = data.aws_vpc.bawaan.id
  tags = {
    Name  = "${local.awalan}-api"
    peran = "api"
  }
}

resource "aws_vpc_security_group_ingress_rule" "http_saya" {
  security_group_id = aws_security_group.api.id
  description       = "HTTP dari IP praktikan"
  cidr_ipv4         = var.cidr_saya
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

# TODO C.2  aws_instance.api : dari AMI sendiri, IP publik, SG api, tag peran/versi

resource "aws_instance" "api" {
  ami                         = aws_ami_from_instance.api.id
  instance_type               = "t3.micro"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.api.id]

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name  = "${local.awalan}-api"
    peran = "api"
    versi = var.versi
  }
}

# Latihan 2.1: aws_instance.goreng (count = var.bandingkan_goreng ? 1 : 0)
