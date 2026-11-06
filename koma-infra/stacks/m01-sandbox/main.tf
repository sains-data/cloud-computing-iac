# Modul 01 — stack sandbox. Ikuti naskah Bagian B lalu C.

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# TODO Bagian B: satu server `aws_instance.web`
resource "aws_instance" "web" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = "t3.micro"
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
    Name   = "koma-${var.nim}-m01-web"
    peran  = "web"
    ukuran = "kecil"
  }
}