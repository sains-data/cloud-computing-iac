# Fondasi akun (Modul 01, dijalankan SEKALI dan TIDAK di-destroy selama kursus).
# Anggaran bulanan dengan peringatan e-mail agar kredit Free plan tidak habis diam-diam.
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "nim" {
  type        = string
  description = "NIM pemilik akun"
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

variable "email_peringatan" {
  type        = string
  description = "Alamat e-mail penerima peringatan anggaran"
  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.email_peringatan))
    error_message = "Isi alamat e-mail yang sah."
  }
}

variable "batas_usd" {
  type        = number
  default     = 50
  description = "Batas anggaran bulanan (USD), paling besar 50"
  validation {
    condition     = var.batas_usd > 0 && var.batas_usd <= 50
    error_message = "Batas anggaran praktikum 1-50 USD."
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      kursus       = "komputasi-awan"
      nim          = var.nim
      kelompok     = var.kelompok
      modul        = "m00"
      stack        = "m00-fondasi"
      "managed-by" = "opentofu"
    }
  }
}

resource "aws_budgets_budget" "anggaran" {
  name         = "koma-${var.nim}-anggaran"
  budget_type  = "COST"
  limit_amount = format("%.1f", var.batas_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # Kredit Free plan menutup tagihan; tanpa ini biaya bersih selalu 0 dan peringatan tidak pernah
  # terkirim. Yang dipantau adalah pemakaian kredit.
  cost_types {
    include_credit = false
    include_refund = false
  }

  dynamic "notification" {
    for_each = toset([20, 50, 100])
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.email_peringatan]
    }
  }
}

output "anggaran" {
  value = {
    nama  = aws_budgets_budget.anggaran.name
    batas = "${aws_budgets_budget.anggaran.limit_amount} ${aws_budgets_budget.anggaran.limit_unit}"
  }
}
