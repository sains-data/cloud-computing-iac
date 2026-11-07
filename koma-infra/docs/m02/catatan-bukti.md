# Modul 02 — Catatan Bukti

| Hal | Isi |
|---|---|
| Nama | |
| NIM | |
| Kelompok | `k0_` |
| Kasus | |
| Peninjau PR `m02` (NIM) | |

Isi berkas ini sambil mengerjakan prosedur. Angka dan ID disalin dari keluaran perintah Anda sendiri; contoh di naskah hanya gambaran. Berkas ini ikut di-commit dan masuk `koma-module-02.zip`.

## Dugaan pre-lab

| Dugaan | Isi |
|---|---|
| Waktu siap server goreng dibanding server dari AMI (detik) | |
| Alasan dugaan | |

## Langkah dan bukti

Satu baris per `koma cek m02`. Potret terakhir sebelum mengumpulkan harus potret bersih.

| Potret | Langkah | Keadaan | Waktu (WIB) | Hasil penting (`Latihan lulus` / `Tugas lulus`, cek yang gagal) |
|---|---|---|---|---|
| 1 | C.4.5 | api 2.0.0 dari AMI 2.0.0 | | |
| 2 | D.4 | api 2.1.0, ID baru | | |
| 3 | Latihan 2.1 | api 2.1.0 + server goreng | | |
| 4 | E.2.2 | bersih setelah `tofu destroy` | | |
| 5 | Tugas Langkah 2 | rilis kasus `<versi>` | | |
| 6 | Tugas Langkah 3 | bersih lagi | | |

## Catatan Bagian A

| Hal | Isi |
|---|---|
| AMI publik terbaru (ID dan nama) | |
| `pemilik` (OwnerId) | |
| `virtualisasi`, `ena`, `root` | |
| Hypervisor, vCPU, memori `t2.micro` | |
| Hypervisor, vCPU, memori `t3.micro` | |
| Hypervisor, vCPU, memori `t3.small` | |
| Ukuran user data (`length(local.cloud_init)`) | |

Mengapa pembangun cukup memakai `t3.micro` (satu kalimat):

## Catatan Bagian B

| Hal | Isi |
|---|---|
| `aws_instance.pembangun` Creation complete | |
| `time_sleep.tunggu_cloud_init` Creation complete | |
| `aws_ami_from_instance.api` Creation complete | |
| **Waktu panggang** (jumlah ketiganya) | |
| ID dan nama AMI 2.0.0 | |
| `OwnerId` AMI (sama dengan akun saya?) | |
| Baris `Cloud-init ... Up N seconds` dari log konsol (beserta jamnya) | |

Apakah jeda 120 detik cukup, dan apa buktinya:

## Catatan Bagian C

| Hal | Isi |
|---|---|
| `url_api` | |
| ID instance api | |
| `aws_instance.api` Creation complete | |
| **Waktu siap** dari `koma sehat` (detik) | |
| Jawaban `/versi` (versi dan host) | |
| Aturan masuk security group | |
| Isi `keluar` (IpPermissionsEgress) security group | |

## Catatan Bagian D

| Hal | Sebelum (2.0.0) | Sesudah (2.1.0) |
|---|---|---|
| ID instance api | | |
| IP publik api | | |
| ID AMI | | |

Rantai penggantian 2.0.0 → 2.1.0 (dari `tofu plan`):

| Resource | Simbol aksi | Atribut pemicu (`# forces replacement`) | Resource hulu penyebab |
|---|---|---|---|
| `aws_instance.pembangun` | | | |
| `time_sleep.tunggu_cloud_init` | | | |
| `aws_ami_from_instance.api` | | | |
| `aws_instance.api` | | | |

Baris `Plan:` :

Resource yang dihapus pertama kali dan akibatnya bagi pengguna API:

| Hal | Isi |
|---|---|
| Jam mengetik `yes` (WIB) | |
| Jam `koma sehat` alamat baru SEHAT (WIB) | |
| **Jeda layanan** | |
| Waktu panggang versi 2.1.0 | |
| Waktu siap versi 2.1.0 (`koma sehat`, detik) | |
| `koma sehat` alamat lama selama apply | |

## Catatan Bagian E

| Hal | Isi |
|---|---|
| Ringkasan `tofu destroy` (jumlah resource) | |
| `describe-images --owners self` setelah destroy | |
| `koma sisa`: resource bertag, instance tanpa `managed-by`, snapshot sisa AMI | |
| `bersih_akhir` dan `Tugas lulus` pada potret 4 | |

## Catatan Tugas

| Hal | Isi |
|---|---|
| Versi rilis kasus dan alasannya (rujuk `K-02-*`) | |
| Ukuran server api (`t3.micro`/`t3.small`) dan alasannya | |
| ID AMI publik yang dipakai saat Tugas | |
| Waktu panggang | |
| Waktu siap (`koma sehat`, detik) | |
| ID instance api rilis kasus | |
| Jawaban `/versi` | |
| Tautan *pull request* `modul-02` → `main` | |
| NIM peninjau dan tanggal persetujuan | |
