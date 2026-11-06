# Kasus k04 — Pasar Rakyat Online

> Studi kasus simulasi pedagogis; bukan organisasi nyata. Semua nama, angka, insiden, mitra, dan kebijakan internal fiktif. Rujukan regulasi dipakai sebagai konteks kasus; tafsiran hukum tidak dinilai.

## Peran kelompok dalam cerita

Kelompok Anda adalah tim platform dan data engineering junior di Pasar Rakyat Online (PRO). Tim melapor kepada Head of Platform, satu dari dua SRE yang dimiliki perusahaan, dan bekerja bersama tim data rekomendasi serta tim keuangan. Selama 12 minggu tim membangun platform marketplace dan data PRO sebagai kode di repo `koma-infra`, dari tag `m01` sampai `m10`. Kebijakan efisiensi perusahaan: tidak ada lingkungan yang hidup tanpa pemilik dan alasan; semua lingkungan non-produksi dibongkar setelah dipakai dan dibangun ulang dari repo. Infrastruktur setiap modul diperlakukan sama.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

PRO adalah marketplace untuk usaha mikro, kecil, dan menengah (UMKM) dengan kantor pusat di Palembang. PRO memiliki 92 ribu penjual aktif di Sumatera dan Jawa, 3,1 juta pembeli terdaftar, dan 640 ribu pembeli aktif bulanan. Karyawan berjumlah 1.250 orang, termasuk 400 pendamping UMKM di lapangan dan 38 engineer. Pesanan normal sekitar 85 ribu per hari; promo tanggal kembar menghasilkan hingga 1,4 juta pesanan dalam 24 jam.

### P2 Model bisnis

Pendapatan berasal dari komisi 2,5% per transaksi dan iklan penjual. Marginnya tipis, dan pendanaan lanjutan tertunda, sehingga direksi memotong anggaran infrastruktur 35%. Promo besar membawa sepertiga GMV bulanan; kegagalan satu jam di awal promo dapat menghapus margin bulan itu.

### P3 Proses bisnis utama

1. Penjual mengunggah produk beserta foto; pendamping UMKM membantu penjual baru.
2. Pembeli mencari, memasukkan ke keranjang, memakai voucher, dan checkout.
3. Pembayaran diproses penyedia payment gateway mitra; status masuk lewat webhook.
4. Pesanan diteruskan ke penjual; paket dikirim lewat 6 ekspedisi mitra.
5. Dana diteruskan ke penjual pada H+2 setelah barang diterima.
6. Tim data menyusun rekomendasi dan laporan penjualan per penjual.

### P4 Pemangku kepentingan dan konflik tujuan

- CEO dan Direktur Keuangan: biaya infrastruktur turun 35% dan tidak boleh melampaui batas.
- Tim pemasaran: promo besar sebulan dua kali dan flash sale pukul 00.00.
- Tim engineering: stabilitas checkout; hanya 2 SRE.
- Penjual UMKM: dana cepat cair dan toko tidak diambil alih orang lain.
- Pembeli: checkout cepat dan voucher berlaku.
- Konflik utama: pemasaran menginginkan kapasitas besar setiap promo, sedangkan keuangan menetapkan batas keras. Setelah insiden promo, kapasitas dinaikkan permanen sehingga biaya membengkak; tidak ada yang berani menurunkannya.

### P5 Insiden pemicu

Promo 10.10 dimulai pukul 00.00. Dalam 15 menit pertama beban naik 18 kali lipat; checkout galat 23% selama 47 menit, 31 ribu keranjang gagal dibayar, dan GMV yang hilang diperkirakan Rp 2,8 miliar. Esok harinya engineer menaikkan ukuran semua server secara manual "supaya aman". Server itu tidak pernah diturunkan, dan tagihan bulan berikutnya naik 70%.

### P6 Target 12 minggu

1. Seluruh infrastruktur marketplace didefinisikan sebagai kode dan dapat dibangun ulang dari repo.
2. SLA 99,5% normal dan 99,9% selama jendela promo 24 jam, dengan p95 checkout < 400 ms.
3. Kapasitas naik otomatis saat promo dan turun kembali setelahnya.
4. Total biaya infrastruktur ≤ Rp 95 juta per bulan dan setiap rupiah bertuan.
5. Data penjualan harian tersedia di cloud publik untuk tim data.

## Tabel E — Arsitektur, lokasi, trafik, dan rencana

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | Web dan mobile web; API katalog, keranjang, checkout, dan pesanan; database transaksi; antrean dan worker untuk meneruskan pesanan ke penjual, notifikasi, dan penyelesaian dana; analytics rekomendasi dan laporan penjual serta arsip; object storage foto produk. |
| E2 | Lokasi | Kantor pusat Palembang; engineer tersebar di 6 kota; produksi berjalan di VPS penyedia cloud lokal ditambah satu rak colocation di Jakarta untuk database. Tidak ada pusat data milik sendiri. |
| E3 | Pola trafik | 75% north-south (penelusuran katalog dan foto), 25% east-west. Jalur checkout justru didominasi east-west: satu checkout memanggil voucher, stok, pembayaran, dan pesanan. |
| E4 | Ketersediaan | SLA 99,5% per bulan pada hari biasa; target internal 99,9% selama jendela promo 24 jam. |
| E5 | Latensi | p95 < 400 ms untuk API checkout; katalog dilayani cache dan tidak menjadi target utama. |
| E6 | Kendala tim | 38 engineer, tetapi hanya 2 SRE yang memegang infrastruktur; tidak ada DBA; pengalaman container baik, pengalaman IaC hampir tidak ada. |
| E7 | Jaringan sekarang | Setiap VPS memiliki IP publik sendiri; firewall diatur per server lewat panel penyedia; replika database pernah terbuka ke internet. |
| E8 | Rencana migrasi | Dalam 6 bulan: database tetap di colocation karena biaya tetap lebih murah; komponen stateless dikemas sebagai container dengan autoscaling; cloud publik untuk lonjakan promo, arsip, dan analytics. |

## Tabel S — Storage

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | Database transaksi relasional 2,6 TB; 210 juta baris pesanan; satu primer dan satu replika baca di colocation. |
| S2 | Dokumen bersama | Kontrak penjual dan dokumen pajak ±1,2 TB di layanan berbagi berkas SaaS dengan tautan yang dibagikan bebas. |
| S3 | Analytics | Clickstream ±120 GB per hari; disimpan 13 bulan untuk perbandingan tahun ke tahun. |
| S4 | Unggahan | Foto produk 4,8 juta produk × rata-rata 5 foto, ±96 TB; disajikan lewat CDN. |
| S5 | Backup | Snapshot VPS harian dari penyedia; dump database mingguan; restore belum pernah diuji. |
| S6 | Insiden storage | Foto produk disimpan di disk server web; disk penuh dan situs mati 2 jam. |
| S7 | Tim storage | 2 SRE; pengembang terbiasa dengan API S3. |
| S8 | Rencana storage | Foto ke object storage dengan lifecycle untuk thumbnail; analytics ke cloud publik; database tetap di colocation dengan volume terpisah. |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Publik: katalog, harga, ulasan. Internal: penjualan agregat, kinerja promo. Rahasia: nama, alamat, telepon pembeli; rekening dan NPWP penjual. Data kartu tidak disimpan karena ditangani payment gateway. |
| A2 | Regulasi dan kepatuhan | UU 27/2022 tentang Pelindungan Data Pribadi; ketentuan payment gateway mitra (tokenisasi, PRO tidak menyimpan data kartu); parameter kasus: dokumen transaksi untuk keperluan perpajakan disimpan 10 tahun. |
| A3 | Ancaman utama | Pengambilalihan akun penjual untuk mengalihkan dana; bot yang memborong voucher; database yang terbuka ke internet. |
| A4 | Akses pihak ketiga | Payment gateway (webhook), 6 ekspedisi mitra (API), agensi pemasaran dengan akses analytics. |
| A5 | Rahasia | Kunci tanda tangan webhook pembayaran, kredensial database, kunci API ekspedisi. |
| A6 | Insiden keamanan | Replika database dengan port terbuka dan password lemah ditemukan oleh pemindai internet; tidak ada bukti eksfiltrasi, tetapi investigasi wajib dilakukan dan dilaporkan ke direksi. |

## Tabel L — Aplikasi legacy

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | Pengelola Voucher versi 0.9 di satu server yang dibuat tangan saat promo pertama pada 2022. |
| L2 | Pengguna | Aplikasi Android versi lama (28% pembeli belum memperbarui) yang memanggil alamat tetap; 3 mitra promosi. |
| L3 | Jadwal pakai | 24 jam; sangat sibuk saat promo; sepi 01.00–06.00 di luar hari promo. |
| L4 | Toleransi downtime | Di luar promo jeda ≤ 30 detik masih diterima; selama jendela promo tidak boleh ada peralihan; jendela pemeliharaan 02.00–05.00 di luar hari promo, maksimal 5 menit. |
| L5 | Data | 600 MB kode voucher dan sisa kuota; setiap penukaran mengubah data, sehingga selisih tulisan saat penyalinan dapat menyebabkan voucher terpakai dua kali. |

## Tabel O — Operasi dan observability

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Ketersediaan 99,5% per 30 hari pada hari biasa (anggaran galat 216 menit atau 0,5% permintaan); 99,9% selama jendela promo; p95 checkout < 400 ms; rasio galat ≤ 0,5% hari biasa dan ≤ 0,1% saat promo. |
| O2 | Jam sibuk | 12.00–13.00 dan 19.00–22.00; promo tanggal kembar dan tanggal gajian 00.00–02.00. |
| O3 | Beban puncak | Normal 260 permintaan/detik; flash sale 4.700 permintaan/detik dalam 15 menit pertama (18 kali). |
| O4 | Alert yang diinginkan | Galat checkout; latensi checkout; webhook pembayaran gagal; biaya harian di atas ambang; drift. |
| O5 | Runbook dan insiden | Satu-satunya runbook adalah "naikkan ukuran server" tanpa langkah menurunkan kembali (P5). |
| O6 | Pemegang on-call | 2 SRE bergantian; satu pengembang tambahan per minggu; "war room" selama promo. |

## Tabel G — Tata kelola dan biaya

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-501 Katalog dan Pencarian, CC-502 Checkout dan Pembayaran, CC-610 Data dan Rekomendasi, CC-700 Pemasaran (promo), CC-900 Platform. |
| G2 | Lingkungan | dev, staging, prod; staging hanya boleh hidup pada jam kerja. |
| G3 | Anggaran bulanan | Batas keras total infrastruktur Rp 95 juta per bulan (sebelumnya Rp 146 juta setelah kenaikan 70%); setiap promo boleh menambah maksimal Rp 12 juta, paling banyak 2 promo per bulan. |
| G4 | Kebijakan label | owner, env, cost-center, data-class wajib; resource promo memakai CC-700 agar biaya promo terlihat; data-class rahasia hanya di prod. |
| G5 | Pemasok cloud | VPS penyedia cloud lokal, colocation (bersama diperankan Koma Lab), dan GCP yang memberi kredit awal untuk 4 bulan. |
| G6 | Kekhawatiran lock-in | Kredit awal menggoda untuk memakai layanan khas penyedia; direksi ingin tetap dapat kembali ke VPS lokal bila kredit habis. |

## Tabel H — Hybrid dan integrasi

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Database transaksi dan penyelesaian dana di colocation (E8). |
| H2 | Integrasi antarsistem | Tim data di cloud membutuhkan laporan penjualan harian per penjual dari API on-premises. |
| H3 | Pesan dan event | Setiap pesanan baru menjadi event pada topik pesanan; konsumennya notifikasi penjual, analytics, dan deteksi kecurangan. |
| H4 | Arsip | Laporan harian dan ringkasan transaksi diarsip ke cloud publik; retensi bisnis 10 tahun untuk keperluan pajak. Bucket lab menghapus objek setelah 7 hari. |
| H5 | Kebutuhan cloud publik | GCS untuk arsip dan analytics; Pub/Sub untuk event pesanan; Cloud Run untuk halaman promo dan penerima webhook. |
| H6 | Kegagalan dan aturan perubahan | Colocation terhubung ke cloud publik lewat internet. Bila cloud publik tidak terjangkau 1 hari, checkout harus tetap berjalan. Seorang engineer pernah mengubah ukuran instance promo dari konsol tanpa catatan dan lupa mengembalikannya. |

## Tabel C — Cloud-native dan skala

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API checkout dan katalog (stateless); antrean pesanan; worker notifikasi penjual. |
| C2 | Pola beban | Lonjakan sangat tajam dan singkat (18 kali dalam 15 menit) pada waktu yang diketahui; di luar promo beban rendah. |
| C3 | Kebutuhan skala | API 260 → 4.700 permintaan/detik; worker harus meneruskan 1,4 juta pesanan dalam 24 jam promo. Rencana 30 server aplikasi stateless saat promo. |
| C4 | Rilis bertahap | Fitur voucher baru dicoba pada 5% pembeli, tidak pernah dalam 48 jam sebelum promo. |
| C5 | Kuota | Kuota diturunkan dari anggaran: kapasitas maksimum ditetapkan agar biaya promo tidak melampaui Rp 12 juta. |
| C6 | Serverless | Halaman promo dan penerima webhook kandidat Cloud Run; jumlah instance maksimum wajib dibatasi untuk mencegah *denial of wallet*. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di PRO |
|---|---|
| web | web dan mobile web marketplace |
| API | API checkout; endpoint pesanan = pesanan pembeli |
| database | database transaksi (S1) |
| worker dan antrean | penerus pesanan ke penjual dan notifikasi |
| analytics dan arsip | laporan penjualan harian, arsip di GCS |
| object storage | foto produk (S4) |
| aplikasi legacy M06 | Pengelola Voucher v0.9 |
| Pub/Sub dan Cloud Run | topik pesanan; halaman promo dan webhook |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil kelompok |
|---|---|---|
| M01 | P5, E1, E4 | konvensi nama dan label; katalog ukuran sebagai alat menahan biaya; refaktor tanpa replace |
| M02 | E1, E6, C3 | container atau VM; pull atau push untuk 30 server promo; bake atau fry agar server siap sebelum 00.00 |
| M03 | E3, E7, A3 | dari IP publik per server ke satu pintu masuk; database tanpa akses internet |
| M04 | S1–S8 | model akses per data; foto keluar dari disk web; versioning dan biayanya |
| M05 | A1–A6 | temuan paling berbahaya; letak kunci webhook; kebijakan penolak akses publik |
| M06 | L1–L5 | strategi per komponen; store and load untuk data voucher yang terus berubah; kapan tidak boleh beralih |
| M07 | O1–O6 | ambang 0,4 s; SLO berbeda saat promo; anggaran galat berbasis permintaan |
| M08 | G1–G6 | pusat biaya promo; showback terhadap batas Rp 95 juta; broker dan kredit penyedia |
| M09 | H1–H6 | perilaku checkout bila cloud putus; retensi 10 tahun; perubahan hanya lewat pipeline |
| M10 | C1–C6, O1 | autoscale atau pre-scale; batas maksimum instance dari anggaran; cluster atau serverless |

## Alur babak M01–M10

### Babak 1 — M01: server besar tanpa pemilik

- Pemicu: setelah insiden P5, daftar tagihan menunjukkan 23 server besar tanpa nama yang jelas; tidak ada yang berani mematikannya.
- Tugas tim: membuat repo `koma-infra`, stack sandbox dengan layanan web dan api, label pemilik dan peran, ukuran dari katalog.
- Keputusan: katalog ukuran sebagai batas (bukan angka bebas); `moved` agar server yang sedang melayani tidak diganti.
- Benang data: inventaris sumber data (pesanan, klik, foto, pembayaran; E1).
- Warisan: tag `m01`, konvensi label, `log-keputusan.md`.

### Babak 2 — M02: server siap sebelum pukul 00.00

- Pemicu: menyiapkan server promo secara manual memakan 3 jam dan sering berbeda konfigurasi.
- Tugas tim: mengukur container dan VM, cloud-init, Ansible, image siap pakai.
- Keputusan: container atau VM per komponen; pull atau push untuk 30 server promo (C3); bake atau fry ketika server harus siap dalam hitungan detik.
- Benang data: server aplikasi tidak menyimpan foto atau sesi; insiden S6 menunjukkan akibatnya.
- Warisan: image API untuk M06–M10.

### Babak 3 — M03: replika database di internet

- Pemicu: setiap server memiliki IP publik dan replika database ditemukan pemindai internet (E7, A6).
- Tugas tim: VPC tiga tier, ACL per tier, load balancer; stack jaringan terpisah.
- Keputusan: satu pintu masuk untuk trafik north-south 75%; aturan east-west jalur checkout.
- Benang data: database hanya menerima koneksi dari tier API.
- Warisan: pola stack jaringan dan ACL.

### Babak 4 — M04: foto di luar disk web

- Pemicu: disk server web penuh oleh foto dan situs mati 2 jam (S6).
- Tugas tim: state remote dengan lock, volume database terpisah, dokumen bersama, bucket foto berversi.
- Keputusan: block/file/object untuk S1, S2, S4; apakah versioning sepadan dengan biaya 96 TB foto; siapa membaca bucket state.
- Benang data: pemisahan data transaksi, dokumen, dan objek; biaya penyimpanan sebagai kriteria.
- Warisan: bucket state dan pola volume terpisah.

### Babak 5 — M05: password lemah dan kunci webhook

- Pemicu: investigasi replika database terbuka (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman, password baru, state terenkripsi, Trivy dan Conftest.
- Keputusan: temuan paling berbahaya; letak kunci webhook pembayaran; aturan penolak akses publik.
- Benang data: data pembeli dan rekening penjual sebagai rahasia (A1).
- Warisan: kebijakan Conftest dan enkripsi state.

### Babak 6 — M06: voucher yang tidak boleh terpakai dua kali

- Pemicu: Pengelola Voucher v0.9 harus diganti sebelum promo berikutnya; 28% pembeli memakai aplikasi lama (L1, L2).
- Tugas tim: mengimpor legacy, membangun versi baru dengan volume terpisah, menyalin data, mengalihkan forward, membongkar legacy.
- Keputusan: strategi per komponen; waktu peralihan di luar promo; cara menutup selisih tulisan voucher (L5); kriteria contract.
- Benang data: konsistensi data stateful saat migrasi.
- Warisan: API baru sebagai target monitoring M07.

### Babak 7 — M07: tahu dalam menit pertama promo

- Pemicu: galat 23% selama 47 menit di awal promo (P5).
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang 0,4 s; ambang galat berbeda untuk hari biasa dan promo; `for:` yang pendek saat promo.
- Benang data: metrik bisnis (checkout berhasil) di samping metrik teknis.
- Warisan: aturan SLO untuk canary M10.

### Babak 8 — M08: tagihan naik 70%

- Pemicu: server yang dinaikkan setelah promo tidak pernah diturunkan (P5, G3).
- Tugas tim: modul layanan-web, dev dan prod dari kode yang sama, label wajib, showback, broker Incus dan GCP.
- Keputusan: pemetaan pusat biaya (termasuk CC-700 promo); showback dibandingkan batas Rp 95 juta; broker ketika kredit penyedia habis.
- Benang data: biaya penyimpanan clickstream dan foto per pusat biaya.
- Warisan: modul dan kebijakan tata kelola untuk pipeline M09.

### Babak 9 — M09: perubahan promo yang lupa dikembalikan

- Pemicu: ukuran instance promo diubah dari konsol dan tidak dikembalikan (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip harian.
- Keputusan: kontrak output antarstack; checkout tetap jalan bila GCP putus; retensi 10 tahun dibandingkan lifecycle lab.
- Benang data: laporan penjualan harian sebagai pipeline hybrid; event pesanan sebagai kanal.
- Warisan: pipeline dan stack GCP untuk M10.

### Babak 10 — M10: promo 12.12 dan rebuild dari nol

- Pemicu: promo 12.12 diperkirakan 18 kali beban normal dalam 15 menit (C2, C3).
- Tugas tim: API, antrean, dan worker di cluster sebagai kode; HPA; canary; Cloud Run untuk halaman promo; rebuild dari namespace kosong.
- Keputusan: autoscale atau pre-scale (HPA butuh waktu bereaksi); batas maksimum dari anggaran; cluster atau serverless.
- Benang data: antrean pesanan menyerap lonjakan; pesanan yang belum diproses hilang bila broker tidak persisten.
- Warisan: ADR akhir dan laporan arsitektur marketplace.
