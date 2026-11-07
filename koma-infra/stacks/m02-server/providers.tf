provider "aws" {
  region = var.region

  default_tags {
    tags = {
      kursus       = "komputasi-awan"
      nim          = var.nim
      kelompok     = var.kelompok
      modul        = "m02"
      stack        = "m02-server"
      "managed-by" = "opentofu"
    }
  }
}
