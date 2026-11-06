# koma-infra

Repo praktikum Komputasi Awan (Sains Data ITERA, 2026) milik satu mahasiswa. Seluruh
infrastruktur di akun AWS Anda dibuat dari kode di repo ini dengan OpenTofu.

```text
koma-infra/
├── alat/                  koma CLI (cek, bukti, arsip) — diperbarui tiap modul lewat `koma ambil`
├── stacks/
│   ├── m00-fondasi/       anggaran dan peringatan biaya (sekali, tidak di-destroy)
│   └── m01-sandbox/       Modul 01, dst. satu folder per stack
├── bukti/                 bukti-mNN.json dari `koma cek mNN` (di-commit)
├── docs/mNN/              catatan bukti per modul
├── TIM.md                 kelompok, kasus, peninjau PR
└── log-keputusan.md       keputusan desain K-NN-xxx
```

Perintah `koma` dijalankan dari folder ini:

```bash
python3 alat/koma.py info        # macOS/Linux
```

```powershell
py alat\koma.py info             # Windows
```

Aturan tetap:

1. Akhiri setiap sesi dengan `tofu destroy` pada stack modul, lalu `koma cek mNN` dan `koma sisa`.
2. Jangan commit `terraform.tfvars`, `*.tfstate`, `.terraform/`, atau `.koma/` (sudah di `.gitignore`).
3. Di PC lab bersama, jalankan `aws logout` sebelum meninggalkan komputer.
