# Kasus k05 — NusaBelajar

> Studi kasus simulasi pedagogis; bukan organisasi nyata. Semua nama, angka, insiden, mitra, dan kebijakan internal fiktif. Kasus ini melanjutkan studi kasus Pertemuan 3; fakta yang berasal dari Pertemuan 3 ditandai (P3). Rujukan regulasi dipakai sebagai konteks kasus; tafsiran hukum tidak dinilai.

## Peran kelompok dalam cerita

Pada Pertemuan 3, NusaBelajar baru memutuskan tahap pertama arsitekturnya. Kini perusahaan sudah tumbuh besar, dan kelompok Anda direkrut sebagai tim platform dan data engineering junior. Tim melapor kepada Kepala Platform dan bekerja bersama tim akademik, tim data, dan petugas pelindungan data. Selama 12 minggu tim membangun platform belajar dan data NusaBelajar sebagai kode di repo `koma-infra`, dari tag `m01` sampai `m10`. Prinsip tim sejak Pertemuan 3, "state dipisah dari app agar replika dapat ditambah dan diganti", diperluas menjadi aturan: semua infrastruktur harus dapat dibangun ulang dari repo. Karena itu, infrastruktur setiap modul dibongkar di akhir modul dan dibangun lagi dari kode.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

NusaBelajar adalah platform belajar untuk kampus dan lembaga pelatihan, dengan pelanggan utama di Indonesia (P3). Pada Pertemuan 3 tim teknisnya 7 orang (P3). Setelah kerja sama dengan 46 kampus dan 120 lembaga pelatihan, NusaBelajar kini memiliki 310 ribu pengguna terdaftar, 135 ribu pengguna aktif bulanan, dan 520 karyawan, dengan tim teknis 31 orang. Ujian daring serentak kini mencapai 24.000 peserta. Kantor pusat berada di Bandar Lampung.

### P2 Model bisnis

Pendapatan per pengguna aktif bulanan (P3), ditambah kontrak tahunan dengan kampus yang memuat SLA layanan ujian. Kampus adalah pemilik data mahasiswa; NusaBelajar bertindak sebagai pemroses. Ujian yang gagal berarti ujian ulang bagi ribuan mahasiswa, penalti kontrak, dan risiko kampus tidak memperpanjang kerja sama.

### P3 Proses bisnis utama

1. Dosen merancang kelas dan menerbitkan materi (P3).
2. Mahasiswa belajar: kelas sinkron, materi video, catatan kolaboratif, forum (P3).
3. Tugas dan ujian: mahasiswa mengunggah jawaban; penilaian otomatis untuk kuis, penilaian dosen untuk esai.
4. Nilai dan laporan terbit; notifikasi dikirim (P3).
5. Lapisan pendukung: identity, moderation, notification, support, audit (P3).

### P4 Pemangku kepentingan dan konflik tujuan

- Produk dan akademik: pengalaman belajar, fitur baru, akses cepat dari berbagai wilayah (P3).
- Keuangan: batas biaya bulanan dan alasan untuk setiap kapasitas yang dipesan (P3).
- Operasi TI: sistem yang dapat dipantau, dipulihkan, dan diperbarui dengan tim kecil (P3).
- Pemilik data (kampus dan petugas pelindungan data): kontrol akses, retensi, audit, penanganan insiden (P3).
- Konflik utama: kampus menuntut ujian 99,9% dan bank soal tidak bocor, sedangkan tim produk ingin rilis setiap minggu dan tim keuangan menolak kapasitas besar yang menganggur di luar minggu ujian.

### P5 Insiden pemicu

Insiden awal (P3): Senin 08.05 portal melambat ketika 4.800 mahasiswa mengunggah jawaban dalam 20 menit; server tunggal mencapai 100% CPU, disk hampir penuh, dan notifikasi terkirim ganda. Insiden baru: pada UTS Oktober, empat kampus menjadwalkan ujian serentak. Sebanyak 11.200 jawaban dikirim dalam 9 menit terakhir sebelum batas waktu; 640 unggahan gagal (5,7%), API ujian mengembalikan galat selama 31 menit, dan 38 ribu notifikasi "jawaban diterima" terkirim ganda sehingga mahasiswa ragu jawabannya tercatat.

### P6 Target 12 minggu

1. Seluruh infrastruktur platform didefinisikan sebagai kode dan dapat dibangun ulang dari repo dalam waktu yang memenuhi RTO 2 jam (P3).
2. Layanan login dan ujian 99,9% per bulan (P3) dengan p95 kirim jawaban < 600 ms.
3. Unggahan yang sudah dikonfirmasi tidak pernah hilang (P3); RPO 15 menit terbukti lewat drill.
4. Kapasitas ujian disiapkan dari kalender ujian dan diskalakan otomatis.
5. Rekap aktivitas belajar tersedia di cloud publik untuk tim data tanpa memindahkan jawaban ujian.

## Tabel E — Arsitektur, lokasi, trafik, dan rencana

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | Web dan mobile; API identity, learning, dan assessment (P3); database relasional; antrean dan worker untuk notifikasi, penilaian otomatis, dan laporan (P3); analytics aktivitas belajar dan arsip; object storage untuk materi, video, dan jawaban (P3). |
| E2 | Lokasi | Kantor pusat Bandar Lampung, tim pengembang di 3 kota; platform berjalan di cloud lokal (keputusan tahap pertama P3: Cloud VPS, object storage S3, database pada VM terpisah). Pengguna di 46 kampus mengakses lewat internet. |
| E3 | Pola trafik | Menurut jumlah permintaan: 45% north-south, 55% east-west (API ↔ database ↔ antrean ↔ worker). Menurut volume byte: 92% north-south karena video dan unggahan. |
| E4 | Ketersediaan | Login dan ujian 99,9%; materi media 99,5%; notifikasi 99,0%; analitik best effort (P3). |
| E5 | Latensi | p95 < 600 ms untuk API kirim jawaban (berkas diunggah langsung ke object storage); login dan kelas sensitif latency (P3). |
| E6 | Kendala tim | Tim teknis 31 orang: 18 pengembang, 4 platform (termasuk tim junior), 3 data, 2 QA, 4 dukungan. Tim belum mengoperasikan Kubernetes produksi (P3); baru ada pilot. |
| E7 | Jaringan sekarang | Rancangan segmentasi P3 (public, application, data, management; default deny) baru diterapkan sebagian; worker dan database masih satu jaringan privat tanpa aturan per tier. Kampus terhubung lewat internet dan SSO. |
| E8 | Rencana migrasi | Inti platform tetap di cloud lokal dalam negeri; dalam 9 bulan analytics, arsip, dan sebagian pemrosesan asinkron memakai cloud publik. |

## Tabel S — Storage

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | Database relasional 1,4 TB (akun, kelas, nilai); RPO 15 menit untuk login dan ujian (P3). |
| S2 | Dokumen bersama | Bank soal dosen ±2,2 TB di file share; bersifat rahasia sampai ujian selesai. |
| S3 | Analytics | Event aktivitas belajar ±55 GB per hari; disimpan 4 tahun mengikuti masa studi. |
| S4 | Unggahan | Jawaban tugas dan ujian 64 TB; materi video 210 TB. Batas berkas ujian 30 MB; satu ujian serentak 24.000 peserta × rata-rata 8 MB ≈ 192 GB dalam 20 menit. |
| S5 | Backup | Dump database setiap 6 jam ke object storage di penyedia dan lokasi yang sama; drill belum dilakukan (P3: "ada file cadangan tanpa drill"). |
| S6 | Insiden storage | Disk hampir penuh dan media lokal cepat habis (P3); 640 unggahan gagal saat UTS (P5). |
| S7 | Tim storage | 4 orang platform dan 3 orang data; pengalaman object storage dari demo MinIO Pertemuan 3. |
| S8 | Rencana storage | Media dan jawaban di object storage S3 cloud lokal (P3) dengan salinan ke failure domain berbeda; arsip dan analytics ke GCS. |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Publik: katalog mata kuliah. Internal: materi kuliah. Rahasia: jawaban ujian, nilai, bank soal sebelum ujian. Data pribadi: identitas dan log (P3). Untuk label `data-class`, data pribadi dipetakan ke rahasia. |
| A2 | Regulasi dan kepatuhan | UU 27/2022 tentang Pelindungan Data Pribadi (P3). Kontrak kampus: data mahasiswa milik kampus, disimpan di penyedia dalam negeri yang dapat diaudit, dan dihapus 1 tahun setelah kontrak berakhir. |
| A3 | Ancaman utama | Kebocoran soal sebelum ujian; mahasiswa membuka jawaban atau nilai orang lain; credential stuffing akun mahasiswa. |
| A4 | Akses pihak ketiga | 46 kampus lewat SSO dan integrasi sistem akademik; penyedia notifikasi email dan push; vendor pengawasan ujian daring. |
| A5 | Rahasia | Kunci SSO kampus, kredensial object storage, kunci API notifikasi, passphrase state. |
| A6 | Insiden keamanan | Seorang moderator membuka jawaban ujian tanpa tiket, melanggar matriks role P3. Bank soal satu kampus tersalin ke bucket staging yang dapat dibaca semua pengembang. |

## Tabel L — Aplikasi legacy

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | Layanan Presensi Kelas Sinkron versi 0.9 di satu VPS yang dibuat tangan pada 2023, sebelum keputusan arsitektur P3. |
| L2 | Pengguna | Plugin presensi di LMS 12 kampus mitra dengan alamat tertanam; perubahan alamat butuh persetujuan TI kampus (1–2 semester). Saat kelas berlangsung tercatat ±9.000 presensi per jam. |
| L3 | Jadwal pakai | Senin–Sabtu 07.00–21.00 mengikuti jadwal kuliah; Minggu kosong. |
| L4 | Toleransi downtime | Jeda ≤ 5 detik (presensi dibuka 15 menit di awal kelas dan mahasiswa dapat mengulang); tidak boleh ada peralihan pada minggu UTS dan UAS; Minggu bebas. |
| L5 | Data | 2,8 GB rekap presensi semester berjalan; menjadi dasar syarat ikut ujian (kehadiran 75%), sehingga tidak boleh hilang. |

## Tabel O — Operasi dan observability

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Login dan ujian 99,9% per 30 hari (anggaran 43,2 menit), RTO 2 jam, RPO 15 menit (P3); p95 kirim jawaban < 600 ms; rasio galat ≤ 0,1%. Notifikasi 99,0%, terkirim ≤ 10 menit, tanpa duplikasi. |
| O2 | Jam sibuk | 07.00–09.00 dan 13.00–15.00; 23.30–23.59 menjelang batas pengumpulan tugas; minggu UTS dan UAS. |
| O3 | Beban puncak | Sizing P3: 5.000 pengguna serentak × 0,15 permintaan/detik = 750 permintaan/detik. Sekarang ujian serentak 24.000 peserta, sekitar 3.600 permintaan/detik. |
| O4 | Alert yang diinginkan | Latensi dan galat API ujian; unggahan gagal; umur event notifikasi tertua > 10 menit; duplikasi notifikasi; drift. Alarm terkait tindakan: siapa menerima dan kapan eskalasi (P3). |
| O5 | Runbook dan insiden | Pre-scale ujian dilakukan manual H-1 tanpa daftar periksa; pada UTS satu kampus terlupa. |
| O6 | Pemegang on-call | Jadwal ujian diketahui 2 minggu sebelumnya; on-call wajib selama jendela ujian (2 orang platform dan 1 pengembang assessment). |

## Tabel G — Tata kelola dan biaya

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-301 Learning, CC-302 Assessment, CC-303 Notifikasi, CC-610 Data, CC-900 Platform. |
| G2 | Lingkungan | dev, staging, prod. |
| G3 | Anggaran bulanan | Rp 85 juta per bulan (awal tahap P3: Rp 15 juta); minggu ujian boleh menambah maksimal Rp 20 juta. Bulan lalu tagihan naik 45% karena staging dibuat seukuran prod dan berisi salinan bank soal. |
| G4 | Kebijakan label | owner, env, cost-center, data-class wajib; data-class rahasia hanya di prod; bank soal tidak boleh ada di staging. |
| G5 | Pemasok cloud | Cloud lokal dalam negeri (diperankan Koma Lab) dan GCP region Jakarta. |
| G6 | Kekhawatiran lock-in | Matriks keputusan P3 sudah menimbang lock-in; antarmuka S3 dipilih agar media dapat dipindah. Tim data ingin layanan analytics khas penyedia. |

## Tabel H — Hybrid dan integrasi

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Di cloud lokal (sisi "on-premises" praktikum): database inti, identity, jawaban ujian, bank soal (A2, E8). |
| H2 | Integrasi antarsistem | Tim data di cloud publik membutuhkan rekap aktivitas belajar harian per kelas (agregat) dari API di cloud lokal. |
| H3 | Pesan dan event | Event "tugas dikumpulkan" dan "nilai terbit" diterbitkan dengan idempotency key (P3); konsumennya notifikasi, penilaian otomatis, dan analytics. |
| H4 | Arsip | Rekap harian dan log ujian ter-pseudonim diarsip ke cloud publik; retensi 4 tahun. Bucket lab menghapus objek setelah 7 hari. |
| H5 | Kebutuhan cloud publik | GCS untuk arsip dan analytics; Pub/Sub untuk event; Cloud Run untuk penilaian otomatis kuis atau halaman pengumuman. |
| H6 | Kegagalan dan aturan perubahan | Bila cloud publik tidak terjangkau 1 hari, ujian tetap berjalan dan notifikasi boleh tertunda. Seorang pengembang pernah mengganti nama topik notifikasi dari konsol sehingga 12 ribu notifikasi nilai tidak terkirim. |

## Tabel C — Cloud-native dan skala

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API assessment (stateless); antrean notifikasi dan penilaian otomatis; worker (P3: queue, retry, idempotency). |
| C2 | Pola beban | Burst terjadwal yang diketahui 2 minggu sebelumnya; lonjakan tajam pada jam mulai dan batas pengumpulan (P3). |
| C3 | Kebutuhan skala | 750 → 3.600 permintaan/detik; contoh HPA P3: minimum 2, maksimum 8 replika, target CPU 60%, request 250m. Rencana 20 server aplikasi. |
| C4 | Rilis bertahap | Rilis dicoba dulu pada satu kampus pilot, tidak pernah pada minggu ujian. |
| C5 | Kuota | Namespace platform memakai kuota yang sama dengan lab; maksimum HPA di lab lebih kecil daripada contoh P3. |
| C6 | Serverless | Penilaian otomatis dan pengumuman kandidat Cloud Run; jawaban ujian dan bank soal tidak boleh di cloud publik. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di NusaBelajar |
|---|---|
| web | portal belajar |
| API | API assessment; endpoint pesanan = jawaban yang dikirim |
| database | database inti (S1) |
| worker dan antrean | notifikasi dan penilaian otomatis |
| analytics dan arsip | rekap aktivitas belajar, arsip di GCS |
| object storage | jawaban, materi, video (S4) |
| aplikasi legacy M06 | Layanan Presensi Kelas Sinkron v0.9 |
| Pub/Sub dan Cloud Run | topik tugas dan nilai; penilaian otomatis |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil kelompok |
|---|---|---|
| M01 | P5, E1, E4, E5 | konvensi nama dan label; refaktor tanpa replace saat ujian berlangsung |
| M02 | E1, E6, C3 | container atau VM; pull atau push untuk 20 server; bake atau fry untuk pre-scale ujian |
| M03 | E3, E7, A3 | menuntaskan segmentasi P3; aturan east-west; posisi worker |
| M04 | S1–S8 | model akses per data; RPO 15 menit dibandingkan dump 6 jam; versioning jawaban |
| M05 | A1–A6 | temuan paling berbahaya; bank soal di staging; kebijakan penolak akses publik |
| M06 | L1–L5 | strategi per komponen; waktu peralihan di luar minggu ujian; kriteria contract |
| M07 | O1–O6 | ambang 0,6 s dan 0,1%; insiden 31 menit dibandingkan anggaran 43,2 menit; alert duplikasi notifikasi |
| M08 | G1–G6 | pusat biaya; staging bukan salinan prod; broker untuk beban analytics |
| M09 | H1–H6 | apa yang boleh keluar; perilaku saat cloud publik putus; retensi 4 tahun |
| M10 | C1–C6, O1 | pre-scale dari kalender ditambah HPA; kuota lab dibandingkan contoh P3; cluster atau serverless |

## Alur babak M01–M10

### Babak 1 — M01: dari keputusan P3 ke repo

- Pemicu: arsitektur tahap pertama P3 berjalan, tetapi server dibuat lewat panel penyedia oleh orang berbeda-beda; dua VPS bernama mirip ditemukan tanpa pemilik.
- Tugas tim: membuat repo `koma-infra`, stack sandbox dengan layanan web dan api, label pemilik dan peran, ukuran dari katalog.
- Keputusan: konvensi label; `moved` agar server yang melayani ujian tidak diganti.
- Benang data: inventaris sumber data (akun, jawaban, event belajar, notifikasi; E1).
- Warisan: tag `m01`, konvensi label, `log-keputusan.md`.

### Babak 2 — M02: server ujian siap dari image

- Pemicu: pre-scale H-1 dilakukan manual dan satu kampus terlupa (O5).
- Tugas tim: mengukur container dan VM, cloud-init, Ansible, image siap pakai.
- Keputusan: container atau VM per komponen; pull atau push untuk 20 server; bake agar server ujian siap dalam detik.
- Benang data: server API tanpa data lokal sesuai prinsip P3 "state dipisah dari app".
- Warisan: image API untuk M06–M10.

### Babak 3 — M03: menuntaskan segmentasi P3

- Pemicu: rancangan segmentasi P3 baru diterapkan sebagian; worker dan database tanpa aturan (E7).
- Tugas tim: VPC tiga tier, ACL per tier, load balancer; stack jaringan terpisah.
- Keputusan: aturan east-west untuk 55% permintaan; database hanya dari tier API.
- Benang data: jalur jawaban ujian dari portal sampai database dibuat eksplisit.
- Warisan: pola stack jaringan dan ACL.

### Babak 4 — M04: unggahan yang tidak boleh hilang

- Pemicu: 640 unggahan gagal (P5) dan dump 6 jam tidak memenuhi RPO 15 menit (S5).
- Tugas tim: state remote dengan lock, volume database terpisah, file share bank soal untuk dua server, bucket jawaban berversi.
- Keputusan: block/file/object untuk S1, S2, S4; bagaimana mendekati RPO 15 menit; siapa membaca state.
- Benang data: durabilitas jawaban (P3: tidak boleh hilang setelah dikonfirmasi).
- Warisan: bucket state dan pola volume terpisah.

### Babak 5 — M05: bank soal di bucket staging

- Pemicu: bank soal tersalin ke staging dan moderator membuka jawaban tanpa tiket (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman, password baru, state terenkripsi, Trivy dan Conftest.
- Keputusan: temuan paling berbahaya bagi integritas ujian; letak rahasia; kebijakan penolak akses publik.
- Benang data: klasifikasi P3 diterjemahkan menjadi aturan yang diuji otomatis.
- Warisan: kebijakan Conftest dan enkripsi state.

### Babak 6 — M06: presensi tanpa mengganti plugin kampus

- Pemicu: Layanan Presensi v0.9 harus diganti, tetapi 12 kampus memakai alamat tetap (L1, L2).
- Tugas tim: mengimpor legacy, membangun versi baru dengan volume terpisah, menyalin data, mengalihkan forward, membongkar legacy.
- Keputusan: strategi per komponen; peralihan pada hari Minggu di luar minggu ujian; kriteria contract.
- Benang data: rekap presensi sebagai data yang menentukan hak ikut ujian (L5).
- Warisan: API baru sebagai target monitoring M07.

### Babak 7 — M07: 31 menit galat saat UTS

- Pemicu: API ujian galat 31 menit dan notifikasi ganda (P5).
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang 0,6 s dan 0,1%; `for:` saat jendela ujian; alert duplikasi dan umur notifikasi.
- Benang data: metrik bisnis (unggahan berhasil, keterlambatan notifikasi; P3) sebagai SLO data.
- Warisan: aturan SLO untuk canary M10.

### Babak 8 — M08: staging seukuran prod

- Pemicu: tagihan naik 45% karena staging seukuran prod dan berisi bank soal (G3).
- Tugas tim: modul layanan-web, dev dan prod dari kode yang sama, label wajib, showback, broker Incus dan GCP.
- Keputusan: pemetaan pusat biaya; aturan rahasia hanya prod; kapan analytics lebih tepat di GCP (G6).
- Benang data: biaya penyimpanan video dan event per pusat biaya.
- Warisan: modul dan kebijakan tata kelola untuk pipeline M09.

### Babak 9 — M09: topik notifikasi yang diganti nama

- Pemicu: 12 ribu notifikasi nilai tidak terkirim karena nama topik diganti dari konsol (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip harian.
- Keputusan: data yang boleh keluar (agregat, ter-pseudonim); perilaku bila cloud publik putus; retensi 4 tahun.
- Benang data: rekap harian sebagai pipeline hybrid; event dengan idempotency key sebagai kanal.
- Warisan: pipeline dan stack GCP untuk M10.

### Babak 10 — M10: UAS 24.000 peserta dan rebuild dari nol

- Pemicu: UAS serentak 24.000 peserta diumumkan 2 minggu sebelumnya (C2, C3).
- Tugas tim: API, antrean, dan worker di cluster sebagai kode; HPA; canary; Cloud Run; rebuild dari namespace kosong.
- Keputusan: pre-scale dari kalender ditambah HPA; canary di kampus pilot; cluster atau serverless; apakah rebuild memenuhi RTO 2 jam.
- Benang data: antrean memisahkan pengiriman jawaban dari notifikasi; pesan yang belum diproses hilang bila broker tidak persisten.
- Warisan: ADR akhir dan laporan arsitektur platform.
