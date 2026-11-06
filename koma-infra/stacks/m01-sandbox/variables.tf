variable "nim" {
  type        = string
  description = "NIM praktikan; dipakai di tag dan nama resource"
  validation {
    condition     = can(regex("^[0-9]{8,10}$", var.nim))
    error_message = "NIM harus 8-10 digit angka."
  }
}

variable "kelompok" {
  type        = string
  description = "ID kelompok kasus (k01-k05; k00 contoh dosen)"
  validation {
    condition     = can(regex("^k0[0-5]$", var.kelompok))
    error_message = "Kelompok harus k01-k05 (k00 untuk contoh dosen)."
  }
}

variable "region" {
  type        = string
  default     = "ap-southeast-2"
  description = "Region proyek AWS (Indonesia: ap-southeast-2)"
}

# TODO Bagian C: tambahkan variabel `layanan` (map(object({ peran, ukuran, os })))
variable "layanan" {
  description = "Katalog server sandbox: kunci = nama pendek, nilai = peran, ukuran preset, dan OS"
  type = map(object({
    peran  = string
    ukuran = string
    os     = optional(string, "al2023")
  }))
  default = {
    web = { peran = "web", ukuran = "kecil" }
    api = { peran = "api", ukuran = "kecil" }
  }

  validation {
    condition     = alltrue([for k in keys(var.layanan) : can(regex("^[a-z][a-z0-9-]{1,19}$", k))])
    error_message = "Kunci layanan: huruf kecil, angka, dan tanda hubung, 2-20 karakter."
  }
  validation {
    condition     = alltrue([for l in values(var.layanan) : contains(["kecil", "sedang"], l.ukuran)])
    error_message = "Ukuran hanya boleh kecil (t3.micro) atau sedang (t3.small)."
  }
  validation {
    condition     = alltrue([for l in values(var.layanan) : contains(["web", "api", "worker", "db"], l.peran)])
    error_message = "Peran hanya boleh web, api, worker, atau db."
  }
  validation {
    condition     = alltrue([for l in values(var.layanan) : contains(["al2023", "debian12"], l.os)])
    error_message = "OS hanya boleh al2023 atau debian12."
  }
}
