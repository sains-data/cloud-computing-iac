# Kasus k02 — Kirim Cepat Andalas

> Studi kasus simulasi pedagogis; bukan organisasi nyata. Semua nama, angka, insiden, mitra, dan kebijakan internal fiktif.

## Peran kelompok dalam cerita

Kelompok Anda adalah tim platform dan data engineering junior di Direktorat Teknologi Kirim Cepat Andalas (KCA). Tim melapor kepada Kepala Platform dan bekerja dekat dengan tim data yang selama ini mengolah laporan dengan lembar kerja. Selama 12 minggu tim membangun platform pelacakan dan pipeline event KCA sebagai kode di repo `koma-infra`, dari tag `m01` sampai `m10`. Aturan direktorat: lingkungan non-produksi dibongkar setiap akhir sprint dan dibangun ulang dari repo; infrastruktur setiap modul diperlakukan sama.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

KCA adalah perusahaan ekspedisi darat dan pengantaran last-mile di Sumatera. KCA mengoperasikan 14 hub sortir, 390 cabang, dan bekerja sama dengan 2.600 agen mitra. Karyawan tetap berjumlah 7.800 orang ditambah 6.200 kurir. Volume normal 410 ribu paket per hari dan mencapai 1,1 juta paket per hari pada dua minggu menjelang Lebaran.

### P2 Model bisnis

Pendapatan berasal dari tarif per kilogram dan zona, kontrak dengan 1.900 pengirim korporat, dan integrasi API dengan 4 marketplace mitra. Layanan bayar di tempat (COD) menyumbang 31% paket; dana COD harus direkonsiliasi dan disetor ke penjual paling lambat H+2. Marketplace mitra menilai KCA dari ketepatan status pelacakan; status yang tertahan berarti penalti kontrak dan pembayaran yang ditahan.

### P3 Proses bisnis utama

1. Paket diterima di agen atau dijemput kurir; resi dibuat lewat aplikasi agen atau API mitra.
2. Paket dipindai di setiap titik: agen, hub asal, linehaul, hub tujuan, cabang, kurir. Rata-rata satu paket menghasilkan 11 event pemindaian dan status.
3. Kurir mengantar dan mengambil foto bukti terima (POD).
4. Dana COD direkonsiliasi; status akhir dikirim ke marketplace lewat webhook.
5. Tim data menyusun laporan ketepatan waktu per hub dan rute.

### P4 Pemangku kepentingan dan konflik tujuan

- Direktur Operasi: pemindaian di hub tidak boleh tertahan walau satu detik pun karena sortir malam berjalan menurut jadwal truk.
- Direktur Komersial: API mitra dan webhook marketplace harus memenuhi SLA kontrak 99,9%.
- Direktur Keuangan: rekonsiliasi COD tepat waktu dan biaya cloud musiman terkendali.
- Tim data: membutuhkan event mentah yang lengkap dan dapat diputar ulang.
- Agen dan kurir: aplikasi harus tetap bekerja pada sinyal lemah.
- Konflik utama: tim data menginginkan semua event mentah disimpan lama, sedangkan kontrak marketplace mewajibkan data pribadi penerima dimasking 90 hari setelah paket terkirim. Operasi ingin kapasitas besar sepanjang tahun, sedangkan Keuangan hanya menyetujui kenaikan kapasitas musiman.

### P5 Insiden pemicu

Kamis sebelas hari menjelang Lebaran, worker tunggal yang memproses event pemindaian mati pukul 23.10 di tengah sortir malam. Antrean event tertahan 6 jam; status 380 ribu paket tidak bergerak di pelacakan. Call center menerima 14.000 panggilan dalam sehari dan satu marketplace menahan pembayaran selama seminggu. Saat worker dijalankan ulang, 6.200 event yang tersimpan di antrean lokal server hilang.

### P6 Target 12 minggu

1. Seluruh infrastruktur pipeline pelacakan didefinisikan sebagai kode dan dapat dibangun ulang dari repo.
2. API pemindaian dan API mitra memenuhi SLA 99,9% dengan p95 < 200 ms.
3. Status tampil di pelacakan paling lambat 2 menit setelah pemindaian (p95).
4. Tidak ada event yang hilang ketika worker atau server mati.
5. Event dan rekap harian tersedia di cloud publik untuk tim data, dengan data pribadi dimasking sesuai kontrak.

## Tabel E — Arsitektur, lokasi, trafik, dan rencana

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | Web pelacakan publik; API (resi, pemindaian, tarif, mitra); database operasional; antrean event dan worker (pembaruan status, notifikasi, webhook marketplace); analytics ketepatan waktu dan data lake; object storage foto POD dan label resi. |
| E2 | Lokasi | Kantor pusat dan pusat data di Padang; ruang server cadangan di Pekanbaru; 14 hub (antara lain Medan, Pekanbaru, Palembang, Jambi, Bandar Lampung) dan 390 cabang terhubung VPN broadband; kurir dan agen memakai jaringan seluler. |
| E3 | Pola trafik | 60% north-south (pemindai, aplikasi kurir dan agen, API mitra, pelacakan publik), 40% east-west (API ↔ antrean ↔ worker ↔ database). Trafik north-south didominasi permintaan kecil (±1,2 KB per event). |
| E4 | Ketersediaan | SLA 99,9% per bulan untuk API pemindaian dan API mitra; pelacakan publik 99,5%; laporan analytics boleh tertunda hingga 6 jam. |
| E5 | Latensi | p95 < 200 ms untuk endpoint penerimaan event pemindaian; pemindai genggam menganggap gagal setelah 1 detik. |
| E6 | Kendala tim | Direktorat Teknologi 26 orang: 6 infrastruktur, 3 DBA, 12 pengembang, 5 analis data. Tim data belum pernah mengelola pipeline; laporan disusun dengan lembar kerja. |
| E7 | Jaringan sekarang | Hub dan cabang memakai segmen flat; pusat data memakai dua segmen (DMZ dan internal); API, worker, dan database berada di segmen internal yang sama. |
| E8 | Rencana migrasi | Dalam 6 bulan, pelacakan publik, webhook marketplace, dan analytics pindah ke cloud publik. Database operasional dan API pemindaian tetap di pusat data Padang 18 bulan karena latensi ke hub dan biaya egress. |

## Tabel S — Storage

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | Database operasional relasional 3,9 TB; tabel status 2,1 miliar baris dengan partisi bulanan; disk lokal dua server di Padang. |
| S2 | Dokumen bersama | Manifest linehaul dan kontrak mitra ±2 TB pada satu NAS di Padang, diakses 14 hub. |
| S3 | Analytics | Event pelacakan ±4,5 juta per hari normal (12 juta menjelang Lebaran), JSON ±4 KB, sekitar 18 GB per hari; tim data ingin menyimpan 3 tahun. |
| S4 | Unggahan | Foto POD 410 ribu per hari × ±180 KB ≈ 74 GB per hari; disimpan 1 tahun untuk sengketa (±27 TB). |
| S5 | Backup | Dump database malam 01.00–04.00, bersamaan dengan puncak sortir malam 22.00–04.00, ke NAS yang sama. |
| S6 | Insiden storage | Disk server worker penuh oleh foto POD sementara; antrean lokal di server worker hilang saat restart (6.200 event, P5). |
| S7 | Tim storage | 3 DBA dan 6 infrastruktur; dua orang pernah memakai object storage kompatibel S3. |
| S8 | Rencana storage | Foto POD ke object storage dengan lifecycle 1 tahun; event mentah ke data lake di cloud publik; database tetap on-premises. |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Publik: status pelacakan tanpa identitas. Internal: rute, manifest, kinerja hub. Rahasia: nama, alamat, nomor telepon penerima, nilai COD, foto POD (memuat wajah dan rumah). |
| A2 | Regulasi dan kepatuhan | UU 27/2022 tentang Pelindungan Data Pribadi; kontrak marketplace mewajibkan data pribadi penerima dimasking 90 hari setelah paket terkirim. Tidak ada kewajiban lokasi data, tetapi region Jakarta diutamakan. |
| A3 | Ancaman utama | Enumerasi nomor resi di API pelacakan untuk mengumpulkan alamat; kebocoran API key mitra; penyalahgunaan akun agen. |
| A4 | Akses pihak ketiga | 4 marketplace dan 1.900 pengirim korporat memakai API key; 2.600 agen memakai akun aplikasi; vendor pemindai genggam memiliki akses manajemen perangkat. |
| A5 | Rahasia | Lebih dari 1.900 API key mitra, kredensial database, token notifikasi push, kunci tanda tangan webhook. |
| A6 | Insiden keamanan | API key salah satu marketplace tertulis di repo publik milik pengembang kontrak dan dipakai pihak luar menarik 220 ribu data penerima selama 9 hari. |

## Tabel L — Aplikasi legacy

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | API Cek Tarif versi 0.9 di satu server yang dibuat tangan pada 2020 di pusat data Padang. |
| L2 | Pengguna | Aplikasi kasir 2.600 agen (35% agen masih memakai versi lama yang alamatnya tertanam) dan 140 pengirim korporat lewat integrasi langsung. |
| L3 | Jadwal pakai | 24 jam; paling sepi 02.00–05.00. |
| L4 | Toleransi downtime | Aplikasi agen mencoba ulang 3 kali dengan jeda 5 detik, sehingga jeda ≤ 15 detik tidak terasa; di atas 15 detik transaksi agen gagal. Tidak ada jendela pemeliharaan resmi. |
| L5 | Data | Tabel tarif 1,4 juta baris rute × layanan (±800 MB) ditambah log; tabel diperbarui seminggu sekali setiap Senin 03.00, di luar itu hanya dibaca. |

## Tabel O — Operasi dan observability

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Ketersediaan 99,9% per 30 hari (anggaran galat 43,2 menit); p95 penerimaan event < 200 ms; rasio galat ≤ 0,1%. Kesegaran: status tampil di pelacakan ≤ 2 menit setelah pemindaian (p95). |
| O2 | Jam sibuk | 22.00–04.00 sortir hub (event pemindaian); 09.00–12.00 penjemputan; 19.00–22.00 pelacakan publik. |
| O3 | Beban puncak | Event pemindaian: normal 600 per detik pada puncak harian, 1.900 per detik menjelang Lebaran. Pelacakan publik: 350 permintaan/detik normal, 2.400 permintaan/detik pada promo marketplace 12.12. |
| O4 | Alert yang diinginkan | Latensi penerimaan event di atas 0,2 s; galat di atas 0,1%; API atau worker mati; panjang antrean dan umur event tertua > 2 menit; drift. |
| O5 | Runbook dan insiden | Insiden P5 diketahui setelah 6 jam lewat call center. NOC hanya memantau ping server, bukan antrean. |
| O6 | Pemegang on-call | NOC 24 jam (2 shift, 4 orang) tanpa hak mengubah infrastruktur; 1 engineer on-call bergilir mingguan. |

## Tabel G — Tata kelola dan biaya

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-410 Operasi Hub, CC-420 Last-mile, CC-510 Integrasi Mitra, CC-610 Data dan Analytics, CC-900 Platform. |
| G2 | Lingkungan | dev, staging, prod; ditambah lingkungan uji beban sementara sebelum musim Lebaran. |
| G3 | Anggaran bulanan | Cloud publik Rp 160 juta per bulan; Keuangan menyetujui dua kali lipat selama 6 minggu musim Lebaran. Tahun lalu lingkungan uji beban tidak dibongkar selama 4 bulan dan tagihan naik 38%. |
| G4 | Kebijakan label | owner, env, cost-center, data-class wajib; data-class rahasia hanya di prod; lingkungan uji beban wajib dibongkar setelah dipakai. |
| G5 | Pemasok cloud | Pusat data Padang (diperankan Koma Lab) dan GCP region Jakarta. |
| G6 | Kekhawatiran lock-in | Data lake harus memakai format terbuka (JSON atau Parquet) agar dapat dipindah; tim data ingin memakai layanan analytics terkelola milik penyedia. |

## Tabel H — Hybrid dan integrasi

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Database operasional dan API pemindaian di Padang (E8). |
| H2 | Integrasi antarsistem | Tim data di cloud membutuhkan rekap harian ketepatan waktu per hub dari API on-premises. |
| H3 | Pesan dan event | Setiap pemindaian menjadi event pada topik status kiriman; konsumennya pembaru status, webhook marketplace, dan analytics. |
| H4 | Arsip | Rekap harian dan event mentah diarsip ke cloud publik; retensi bisnis 3 tahun, data pribadi dimasking setelah 90 hari. Bucket lab menghapus objek setelah 7 hari. |
| H5 | Kebutuhan cloud publik | GCS untuk arsip dan data lake; Pub/Sub untuk fan-out event ke tiga konsumen; Cloud Run untuk pelacakan publik dan webhook marketplace. |
| H6 | Kegagalan dan aturan perubahan | Bila cloud publik tidak terjangkau, event harus ditahan di sisi on-premises hingga 6 jam (sekitar 13 juta event pada 600 per detik). Seorang engineer pernah menghapus langganan topik dari konsol saat "bersih-bersih", dan marketplace tidak menerima pembaruan status selama 5 jam. |

## Tabel C — Cloud-native dan skala

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API penerimaan event (stateless); antrean event; worker pembaru status dan pengirim webhook. |
| C2 | Pola beban | Siklik harian dengan puncak malam; musiman 2,7 kali menjelang Lebaran; lonjakan pelacakan publik saat promo marketplace. |
| C3 | Kebutuhan skala | Worker harus mengikuti 1.900 event per detik dan mampu menghabiskan tumpukan setelah gangguan. Rencana 56 server penerimaan event (4 per hub). |
| C4 | Rilis bertahap | Versi baru diuji dulu di hub Pekanbaru, lalu diperluas; tidak ada rilis selama 3 minggu menjelang Lebaran. |
| C5 | Kuota | Namespace platform berbagi cluster dengan tim lain; kuota sama dengan lab. |
| C6 | Serverless | Pelacakan publik dan webhook marketplace kandidat Cloud Run karena lonjakan tajam dan dapat diskalakan terpisah; penerimaan event hub tetap dekat database. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di KCA |
|---|---|
| web | pelacakan publik |
| API | API pemindaian; endpoint pesanan = event pemindaian |
| database | database operasional (S1) |
| worker dan antrean | pembaru status dan webhook marketplace |
| analytics dan arsip | rekap ketepatan waktu, data lake di GCS |
| object storage | foto POD (S4) |
| aplikasi legacy M06 | API Cek Tarif v0.9 |
| Pub/Sub dan Cloud Run | topik status kiriman; pelacakan publik dan webhook |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil kelompok |
|---|---|---|
| M01 | P5, E1, E4, E5 | konvensi nama dan label; refaktor tanpa replace pada API yang menerima event 24 jam |
| M02 | E1, E2, C3 | container atau VM per komponen; pull atau push untuk 56 server di 14 hub; bake atau fry |
| M03 | E3, E7, A3 | segmentasi tier ketika trafik dominan north-south; pintu masuk tunggal untuk pemindai dan mitra |
| M04 | S1–S8 | model akses per data; jadwal backup yang bentrok dengan sortir; lifecycle foto POD |
| M05 | A1–A6 | temuan paling berbahaya; letak dan rotasi API key; kebijakan yang menolak akses publik |
| M06 | L1–L5 | strategi per komponen; store and load untuk data yang hampir statis; jeda terhadap retry 15 detik |
| M07 | O1–O6 | ambang 0,2 s; alert umur event; anggaran 43,2 menit dibandingkan insiden 6 jam |
| M08 | G1–G6 | pusat biaya; aturan rahasia hanya prod; pembongkaran lingkungan uji beban; broker untuk analytics |
| M09 | H1–H6 | outbox saat cloud putus; masking 90 hari; retensi 3 tahun dibandingkan lifecycle lab |
| M10 | C1–C6, O1 | jumlah worker untuk mengejar tumpukan; canary di satu hub; cluster atau serverless |

## Alur babak M01–M10

### Babak 1 — M01: dua server worker yang tidak dikenal

- Pemicu: setelah insiden P5 ditemukan dua server worker cadangan yang dibuat tangan; tidak ada yang tahu mana yang terhubung ke antrean produksi.
- Tugas tim: membuat repo `koma-infra`, stack sandbox dengan layanan web dan api, label pemilik dan peran, ukuran dari katalog.
- Keputusan: konvensi nama dan label; `moved` agar API yang menerima event 24 jam tidak diganti saat refaktor.
- Benang data: setiap server diberi label peran sehingga sumber event (pemindaian, mitra, pelacakan; E1) dapat dipetakan.
- Warisan: tag `m01` dan konvensi label untuk 56 server hub.

### Babak 2 — M02: 56 server hub yang sama persis

- Pemicu: rencana 56 server penerimaan event di 14 hub (C3); konfigurasi antarhub sering berbeda.
- Tugas tim: mengukur container dan VM, cloud-init, Ansible, image siap pakai.
- Keputusan: container atau VM per komponen; pull atau push untuk server di hub dengan VPN broadband (E2); bake atau fry untuk mengganti server saat sortir malam.
- Benang data: server penerimaan event tidak menyimpan event secara lokal; insiden S6 menunjukkan akibatnya.
- Warisan: image API yang dipakai ulang di M06–M10.

### Babak 3 — M03: satu pintu untuk pemindai dan mitra

- Pemicu: worker, API, dan database di segmen yang sama; API mitra dapat dijangkau langsung tanpa melewati load balancer (E7).
- Tugas tim: VPC tiga tier, ACL per tier, load balancer di depan web; stack jaringan terpisah.
- Keputusan: segmentasi ketika 60% trafik north-south (E3); aturan east-west antara API, antrean, dan database.
- Benang data: jalur ingest event dibuat eksplisit dari tepi sampai database.
- Warisan: pola stack jaringan dan ACL.

### Babak 4 — M04: event yang tidak hilang saat restart

- Pemicu: 6.200 event hilang karena antrean lokal di disk worker (S6); backup bentrok dengan sortir malam (S5).
- Tugas tim: state remote dengan lock, volume data terpisah, dokumen manifest bersama, bucket foto POD berversi.
- Keputusan: block/file/object untuk S1, S2, S4; jadwal backup; lifecycle foto POD 1 tahun.
- Benang data: pemisahan penyimpanan event, transaksi, dan objek; durabilitas data yang sedang dalam perjalanan.
- Warisan: bucket state kelompok dan pola volume terpisah.

### Babak 5 — M05: API key di repo publik

- Pemicu: kebocoran 220 ribu data penerima lewat API key di repo publik (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman, membangkitkan rahasia baru, mengenkripsi state, memasang Trivy dan Conftest.
- Keputusan: temuan paling berbahaya; rotasi 1.900 API key; aturan yang menahan bucket foto POD publik.
- Benang data: alamat dan telepon penerima sebagai data rahasia (A1) yang harus dimasking (A2).
- Warisan: kebijakan Conftest dan enkripsi state.

### Babak 6 — M06: API tarif tanpa mengganti aplikasi agen

- Pemicu: API Cek Tarif v0.9 harus diganti, tetapi 35% agen memakai aplikasi lama dengan alamat tertanam (L2).
- Tugas tim: mengimpor legacy, membangun versi baru dengan volume terpisah, menyalin tabel tarif, mengalihkan forward, membongkar legacy.
- Keputusan: strategi per komponen; waktu salin di luar Senin 03.00; kriteria contract.
- Benang data: data tarif yang hampir statis memudahkan store and load; validasi jumlah baris setelah salin.
- Warisan: API baru sebagai target monitoring M07.

### Babak 7 — M07: NOC melihat antrean, bukan hanya ping

- Pemicu: insiden P5 diketahui setelah 6 jam (O5).
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang 0,2 s dan 0,1%; `for:` yang realistis; alert umur event tertua sebagai sinyal kesegaran.
- Benang data: kesegaran status (≤ 2 menit) menjadi SLO data, bukan hanya SLO API.
- Warisan: aturan SLO untuk menilai canary di M10.

### Babak 8 — M08: lingkungan uji beban yang terlupa

- Pemicu: tagihan naik 38% karena lingkungan uji beban hidup 4 bulan (G3).
- Tugas tim: modul layanan-web, lingkungan dev dan prod dari kode yang sama, label wajib, showback, broker Incus dan GCP.
- Keputusan: pemetaan pusat biaya; aturan rahasia hanya prod; kapan beban analytics lebih tepat di GCP.
- Benang data: biaya penyimpanan event dan foto per pusat biaya; label `data-class` pada data lake.
- Warisan: modul dan kebijakan tata kelola untuk pipeline M09.

### Babak 9 — M09: langganan yang dihapus dari konsol

- Pemicu: langganan topik dihapus manual dan marketplace tidak menerima status 5 jam (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip harian.
- Keputusan: kontrak output antarstack; perilaku bila GCP putus (outbox 6 jam); masking sebelum data keluar.
- Benang data: pipeline hybrid event dan rekap harian (H2–H4).
- Warisan: pipeline dan stack GCP dipakai ulang di M10.

### Babak 10 — M10: musim Lebaran dan rebuild dari nol

- Pemicu: musim Lebaran 2,7 kali beban normal dan tumpukan event setelah gangguan (C2, C3).
- Tugas tim: API, antrean, dan worker di cluster sebagai kode; HPA; canary; Cloud Run; rebuild dari namespace kosong.
- Keputusan: jumlah worker untuk menghabiskan tumpukan; canary di hub Pekanbaru; cluster atau serverless untuk pelacakan publik.
- Benang data: antrean memisahkan penerimaan event dari pembaruan status; event yang belum diproses hilang bila broker tidak persisten.
- Warisan: ADR akhir dan laporan arsitektur pipeline pelacakan.
