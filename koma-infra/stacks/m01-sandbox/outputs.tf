# TODO Bagian B: output id dan IP privat server web.
# TODO Bagian C: ganti menjadi map per kunci layanan.
output "web" {
  description = "Server web sandbox"
  value = {
    id        = aws_instance.web.id
    ip_privat = aws_instance.web.private_ip
  }
}