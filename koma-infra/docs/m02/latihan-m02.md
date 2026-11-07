# Latihan 2.1 — Goreng atau panggang

| Hal | Isi |
|---|---|
| Nama | |
| NIM | |
| Kelompok | `k0_` |
| Kasus | |

Berkas ini ditulis sendiri dan diunggah bersama `bukti/bukti-m02.json` ke **Latihan Mandiri di Lab — Modul 02**. Angka berasal dari akun dan terminal Anda sendiri.

## 1. Kode server goreng

Salin `aws_instance.goreng` dan output `url_goreng` yang Anda tulis.

```hcl

```

`tofu plan` dengan `bandingkan_goreng = false` (salin baris ringkasannya):

```text

```

## 2. Pengukuran

Waktu siap diukur dengan `koma sehat` yang dijalankan segera setelah apply selesai.

| Server | Sumber AMI | "Creation complete" | `koma sehat` (detik) | Total sampai sehat | Jawaban `/versi` |
|---|---|---|---|---|---|
| api 2.0.0 (C.4) | AMI milik sendiri | | | | |
| api 2.1.0 (D.3) | AMI milik sendiri | | | | |
| goreng 2.1.0 (Latihan) | AMI publik + user data | | | | |

Selisih rata-rata waktu siap server goreng dibanding server api: ... detik. Dugaan pre-lab saya: ... detik.

## 3. Mengapa selisihnya sebesar itu

Uraikan apa yang dikerjakan cloud-init di server goreng sebelum `/health` menjawab, dan mengapa server api tidak perlu menunggu langkah yang sama.

Bagaimana selisih ini berubah bila template harus memasang paket (misalnya `dnf install`) saat boot? Kaitkan dengan isi `keluar` security group yang Anda catat di C.4.4.

## 4. Kapan fry masih masuk akal

Untuk kasus kelompok Anda, sebut konfigurasi yang masuk akal tetap digoreng dan yang harus dipanggang (Morris, 2025, hlm. 198). Rujuk kode bukti kasus (C3, E2, E6).

## 5. Bukti

- Potret 3 (server goreng hidup) pada (WIB):
- `grep -c "m02-goreng" bukti/bukti-m02.json` menghasilkan:
- `bandingkan_goreng` dikembalikan ke `false` dan server goreng terhapus: ya / belum
- `latihan_lulus` pada `bukti/bukti-m02.json` setelah Bagian E:
