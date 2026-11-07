# Jawaban Analisis — Modul 02 (draf)

| Hal | Isi |
|---|---|
| Nama | |
| NIM | |
| Kelompok | `k0_` |
| Kasus | |

Draf ini ditulis sendiri, lalu disalin ke jendela **Soal analisis** pada **Tugas Individu — Modul 02** di Workbench. Bukti berasal dari pekerjaan Anda (`docs/m02/catatan-bukti.md`) dan berkas kasus kelompok. Sebut kode bukti kasus (E1, E2, E4, E5, E6, C3, A1, A3) saat memakai angkanya, dan rujuk baris `K-02-*` bila relevan.

## Pertanyaan 1 — Hypervisor, Nitro, dan overhead

Bukti dari Bagian A (hypervisor, `virtualisasi`, `ena` untuk `t2.micro`, `t3.micro`, `t3.small`):

Jalur panggilan dan letak overhead ketika `koma_api.py` menjawab permintaan; apa yang dilakukan Nitro (Surianarayanan & Chelliah, 2023, hlm. 82–86; Kumar & Singh, 2025, hlm. 280):

| Komponen kasus (E1) | VM (instance) sendiri atau berbagi VM sebagai container (Modul 08) | Alasan singkat |
|---|---|---|
| | | |
| | | |
| | | |
| | | |

Satu kondisi yang membuat rekomendasi berubah:

## Pertanyaan 2 — Bake atau fry bagi kasus

Bukti (waktu panggang dari Bagian B; waktu siap api dari C.4 dan D.3; waktu siap goreng dari Latihan 2.1):

| Ukuran | Angka saya |
|---|---|
| Waktu panggang | |
| Waktu siap api dari AMI | |
| Waktu siap server goreng | |

Mengapa selisihnya sebesar itu, dan bagaimana bila server harus memasang paket saat boot:

Pilihan untuk kasus (C3, E6, E2), yang dikorbankan, dan dampak memisahkan pembangunan AMI ke pipeline sendiri (Morris, 2025, hlm. 198 dan 203; Hafner, 2025, hlm. 381–382):

## Pertanyaan 3 — Immutable atau mutable, dan SLA kasus

Bukti (rantai penggantian dari `tofu plan` 2.0.0 → 2.1.0, resource yang dihapus pertama, jeda layanan yang diukur):

| Hal | Isi |
|---|---|
| Target E4 kasus | |
| Anggaran waktu tidak tersedia per 30 hari | |
| Jeda layanan per rilis (D.3) | |
| Bagian anggaran yang habis per rilis | |

Perbandingan dengan alternatif mutable; cara immutable server mencegah snowflake (Morris, 2025, hlm. 199–202); yang masih harus ditambahkan:

## Pertanyaan 4 — Risiko keamanan image dan security group

| Risiko | Pada image atau jalan masuk jaringan | Kontrol yang sudah ada di stack saya | Kontrol yang perlu ditambahkan |
|---|---|---|---|
| | image | | |
| | image | | |
| | jaringan | | |
| | jaringan | | |

Kaitan dengan kelas data (A1) dan ancaman utama (A3) kasus (Morris, 2025, hlm. 199 dan 203; Kumar & Singh, 2025, hlm. 283):
