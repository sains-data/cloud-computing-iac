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
#   - ami dari data.aws_ami.al2023
#   - instance_type "t3.micro"
#   - tanpa IP publik
#   - IMDSv2 wajib (metadata_options)
#   - tag Name = "koma-${var.nim}-m01-web" dan peran = "web"
