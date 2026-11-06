# TODO Bagian B: output id dan IP privat server web.
# TODO Bagian C: ganti menjadi map per kunci layanan.
output "instance" {
  description = "Server sandbox per kunci layanan"
  value = {
    for k, i in aws_instance.layanan : k => {
      id        = i.id
      tipe      = i.instance_type
      ip_privat = i.private_ip
      ami       = i.ami
    }
  }
}