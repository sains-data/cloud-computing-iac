variable "nim" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{8,10}$", var.nim))
    error_message = "NIM harus 8-10 digit angka."
  }
}

variable "kelompok" {
  type = string
  validation {
    condition     = can(regex("^k0[0-5]$", var.kelompok))
    error_message = "Kelompok harus k01-k05 (k00 untuk contoh dosen)."
  }
}

variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "versi" {
  type        = string
  default     = "2.0.0"
  description = "Versi koma-api yang dipanggang ke AMI"
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.versi))
    error_message = "Versi berbentuk MAYOR.MINOR.PATCH, mis. 2.1.0."
  }
}

variable "cidr_saya" {
  type        = string
  description = "IP publik komputer praktikan sebagai /32 (keluaran `koma ip`)"
  validation {
    condition     = can(cidrhost(var.cidr_saya, 0)) && endswith(var.cidr_saya, "/32")
    error_message = "Isi dengan satu alamat IPv4 berakhiran /32, mis. 36.70.1.2/32."
  }
}

variable "tunggu_cloud_init" {
  type        = string
  default     = "120s"
  description = "Jeda sebelum AMI dipanggang, agar cloud-init di pembangun selesai"
}

variable "bandingkan_goreng" {
  type        = bool
  default     = false
  description = "Latihan 2.1: luncurkan juga server 'goreng' (AMI publik + cloud-init) sebagai pembanding"
}
