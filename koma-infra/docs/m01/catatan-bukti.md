# Modul 01 — Catatan Bukti

Isi berkas ini segera setelah setiap langkah penting, lalu commit bersama `bukti/bukti-m01.json`.
Waktu ditulis dalam WIB. ID instance disalin dari terminal (`i-0…`); jangan menulis nomor akun AWS.

| Hal | Isi |
|---|---|
| Nama | |
| NIM | |
| Kelompok | `k0_` |
| Kasus | |

## Log langkah

| Langkah | Waktu (WIB) | Perintah | Hasil singkat |
|---|---|---|---|
| A.1 Konsol | | (konsol EC2) | |
| A.2 CLI dua kali | | `aws ec2 run-instances …` | |
| A.3 Cek + bongkar | | `koma cek m01`, `aws ec2 terminate-instances …` | |
| B.1 Anggaran | | `tofu apply m00.tfplan` | |
| B.4 Apply pertama | | `tofu apply m01.tfplan` | |
| B.5 Potret 2 | | `koma cek m01` | |
| C.1 Plan kedua | | `tofu plan -detailed-exitcode` | |
| C.3 Refaktor | | `tofu apply m01.tfplan` | |
| C.4 Potret 3 | | `koma cek m01` | |
| D.1 Destroy + apply | | `tofu destroy`, `tofu apply` | |
| D.1 Potret 4 | | `koma cek m01` | |
| Latihan L.4 (potret 5) | | `tofu apply`, `koma cek m01` | |
| E.1 Destroy + potret 6 | | `tofu destroy`, `koma cek m01`, `koma sisa` | |
| Tugas: katalog kasus | | `tofu apply`, `koma cek m01` | |
| Tugas: destroy akhir | | `tofu destroy`, `koma cek m01` | |

## Catatan Bagian A

- Waktu konsol (klik pertama sampai `Running`): … menit … detik; jumlah isian yang disentuh: …
- Waktu CLI (Enter sampai `running`): … detik
- ID instance: `coba-konsol` …; dua `coba-cli` … dan …
- Keputusan yang tidak tercatat di mana pun selain ingatan dan riwayat terminal saya:
  - …
  - …
- Semua instance Bagian A sudah di-terminate (bukti: `describe-instances` kosong; `tanpa_instance_liar` lulus pada potret …): ya / belum

## Catatan Bagian D

- Plan kedua (C.1): exit code = 
- ID sebelum destroy: `web` …, `api` …
- ID sesudah apply ulang: `web` …, `api` …
- Waktu destroy: … ; waktu apply ulang: …
- Potret yang meluluskan `reproducible`: potret … dan potret …

### Model layanan

| Komponen | IaaS / PaaS / SaaS / bukan model layanan | Alasan (lapisan yang saya sentuh dan yang tidak) |
|---|---|---|
| Instance EC2 | | |
| AWS Budgets | | |
| Repo GitHub | | |
| Workbench (panel Tugas) | | |
| `koma cek` | | |

### Karakteristik cloud yang dialami

| Karakteristik ([S] hlm. 40–45) | Dialami / dibatasi / tidak | Bukti hari ini (perintah, keluaran, atau angka) |
|---|---|---|
| On-demand provisioning | | |
| Self-service | | |
| Resource pooling, multi-tenancy | | |
| Rapid elasticity | | |
| Measured service | | |
| Broad network access | | |

## Potret Tugas

- Katalog kasus (`default` di `variables.tf`): kunci … peran … ukuran …
- Potret aktif katalog kasus: nomor …, waktu …
- Potret bersih terakhir: nomor …, waktu …; `tugas_lulus`: …
