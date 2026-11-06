# Studi Kasus Praktikum Komputasi Awan — Baca Dulu

Setiap kelompok memegang **satu kasus** sepanjang praktikum. Kelompok Anda berperan sebagai tim junior *platform & data engineering* di organisasi pada kasus itu. Semua organisasi, angka, dan insiden di berkas-berkas ini fiktif dan dibuat untuk pembelajaran.

> **Catatan versi 2026.3 (AWS, 8 modul).** Berkas kasus ditulis untuk rancangan awal: 10 modul,
> private cloud yang "diperankan Koma Lab/Incus", dan cloud publik GCP. Mulai 2026.3 setiap
> anggota membangun di akun AWS sendiri, dan praktikum dipadatkan menjadi 8 modul (Modul 06 =
> M06+M07, Modul 07 = M08+M09, Modul 08 = M10). Saat membaca kasus: anggap "Koma Lab/Incus" sebagai
> lingkungan privat organisasi yang tidak Anda bangun, dan padankan layanan GCP dengan AWS
> (GCS → S3, Pub/Sub → SNS/SQS, Cloud Run → Lambda atau ECS Fargate, region Jakarta → region
> akun Anda). Kode bukti (P, E, S, A, L, O, G, H, C) dan angkanya tetap berlaku.

## Berkas

| Berkas | Kelompok |
|---|---|
| `kasus-k00-sumatera-data.md` | contoh kerja dosen; dipakai naskah modul sebagai contoh |
| `kasus-k01-klinik-sehat-lampung.md` | k01 |
| `kasus-k02-kirim-cepat-andalas.md` | k02 |
| `kasus-k03-layanan-publik-way-kanan.md` | k03 |
| `kasus-k04-pasar-rakyat-online.md` | k04 |
| `kasus-k05-nusabelajar.md` | k05 |

Kasus kelompok Anda ditetapkan dosen pada pertemuan praktikum pertama dan dicatat di `TIM.md`. Pakai berkas kasus kelompok Anda sendiri. Berkas k00 hanya contoh cara membaca dan memakai bukti.

## Cara membaca berkas kasus

Semua kasus memakai struktur dan kode yang sama. Naskah modul merujuk kode itu, misalnya "E4 kasus kelompok Anda".

| Bagian | Isi | Modul pemakai utama |
|---|---|---|
| Peran kelompok | posisi tim di organisasi dan aturan bangun ulang dari repo | semua |
| P1–P6 | profil, model bisnis, proses bisnis, pemangku kepentingan, insiden pemicu, target 12 minggu | M01 |
| E1–E8 | arsitektur aplikasi, lokasi, pola trafik, SLA, latensi, kendala tim, jaringan sekarang, rencana migrasi | M01–M03, M07 |
| S1–S8 | data transaksi, dokumen bersama, analytics, unggahan, backup, insiden storage, tim storage, rencana storage | M04 |
| A1–A6 | kelas data, regulasi, ancaman utama, akses pihak ketiga, rahasia, insiden keamanan | M05 |
| L1–L5 | aplikasi legacy: nama, pengguna, jadwal pakai, toleransi downtime, data | M06 |
| O1–O6 | SLO, jam sibuk, beban puncak, alert yang diinginkan, runbook, pemegang on-call | M07 |
| G1–G6 | pusat biaya, lingkungan, anggaran, kebijakan label, pemasok cloud, kekhawatiran lock-in | M08 |
| H1–H6 | sistem yang tetap on-premises, integrasi, pesan dan event, arsip, kebutuhan cloud publik, kegagalan dan aturan perubahan | M09 |
| C1–C6 | komponen yang dipecah, pola beban, kebutuhan skala, rilis bertahap, kuota, serverless | M10 |
| Pemetaan ke aplikasi contoh | wujud komponen lab (web, API, database, worker, arsip, object storage, legacy) di kasus Anda | semua |
| Peta ke modul | modul, kode bukti yang dipakai, dan keputusan yang harus diambil kelompok | semua |
| Alur babak M01–M10 | per modul: pemicu, tugas tim, keputusan, benang data, warisan ke babak berikutnya | semua |

## Aturan pemakaian

- Setiap keputusan, memo, dan jawaban analisis menyebut **kode bukti** yang dipakai (misalnya "menurut E4 dan O1").
- Angka Sumatera Data di naskah adalah contoh. Jawaban Anda memakai angka kasus kelompok Anda.
- Infrastruktur teknisnya sama untuk semua kelompok: nama stack, nama instance, dan cek verifier tidak berbeda. Yang berbeda adalah parameter, keputusan, dan penalarannya.
- Cerita bersambung lewat repo `koma-infra` kelompok. Infrastruktur dibongkar di akhir setiap modul dan dibangun ulang dari kode.
