# Modul 01 — stack sandbox. Ikuti naskah Bagian B lalu C.
locals {
  # Katalog ukuran: mahasiswa memilih nama preset, bukan mengetik tipe instance.
  preset = {
    kecil  = "t3.micro"
    sedang = "t3.small"
  }
  ami = {
    al2023   = data.aws_ami.al2023.id
    debian12 = data.aws_ami.debian12.id
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

data "aws_ami" "debian12" {
  most_recent = true
  owners      = ["136693071363"] # akun resmi Debian
  filter {
    name   = "name"
    values = ["debian-12-amd64-*"]
  }
}

# Refaktor Bagian C: instance tunggal aws_instance.web menjadi anggota for_each
# tanpa dibuat ulang.

resource "aws_instance" "layanan" {
  for_each = var.layanan

  ami                         = local.ami[each.value.os]
  instance_type               = local.preset[each.value.ukuran]
  associate_public_ip_address = false

  metadata_options {
    http_tokens = "required" # IMDSv2
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  tags = {
    Name   = "koma-${var.nim}-m01-${each.key}"
    peran  = each.value.peran
    ukuran = each.value.ukuran
  }
}