provider "aws" {
  region = var.region

  # Tag wajib praktikum dipasang di provider sehingga semua resource mendapatkannya.
  default_tags {
    tags = {
      kursus       = "komputasi-awan"
      nim          = var.nim
      kelompok     = var.kelompok
      modul        = "m01"
      stack        = "m01-sandbox"
      "managed-by" = "opentofu"
    }
  }
}
