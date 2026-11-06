# Kasus k03 — Layanan Publik Kabupaten Way Kanan

> Studi kasus simulasi pedagogis. Nama wilayah dipakai hanya sebagai latar; sistem, angka, insiden, anggaran, dan kebijakan dalam kasus ini fiktif dan tidak menggambarkan pemerintah daerah yang sebenarnya. Rujukan regulasi dipakai sebagai konteks kasus; tafsiran hukum tidak dinilai.

## Peran kelompok dalam cerita

Kelompok Anda adalah tim platform dan data engineering junior yang dibentuk di dinas pengelola teknologi informasi kabupaten (selanjutnya "Dinas TIK") untuk portal layanan publik terpadu. Tim melapor kepada Kepala Bidang Aplikasi dan bekerja bersama dinas perizinan, dinas pendapatan, dan inspektorat. Selama 12 minggu tim menyusun platform layanan dan data portal sebagai kode di repo `koma-infra`, dari tag `m01` sampai `m10`. Ketentuan Dinas TIK: lingkungan non-produksi tidak boleh hidup di luar jam kerja tanpa alasan tertulis dan harus dapat dibangun ulang dari repo; infrastruktur setiap modul diperlakukan sama.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

Pemerintah kabupaten dalam kasus ini melayani sekitar 480 ribu penduduk lewat 31 perangkat daerah, seluruh kantor kecamatan, dan satu Mal Pelayanan Publik (MPP). Portal layanan terpadu dipakai 4.600 ASN dan PPPK sebagai pengguna internal. Setiap tahun portal menerima sekitar 128 ribu permohonan: izin usaha, persetujuan bangunan, izin reklame, surat keterangan, dan pengaduan.

### P2 Model bisnis

Layanan dibiayai APBD dan tidak mencari laba. Keberhasilan diukur dari waktu penyelesaian permohonan, indeks kepuasan masyarakat, dan penerimaan retribusi serta pajak daerah yang dibayar lewat bank mitra pemerintah daerah. Anggaran disusun setahun sekali dan tidak dapat dinaikkan di tengah tahun anggaran.

### P3 Proses bisnis utama

1. Warga mengajukan permohonan lewat portal atau loket MPP dan mengunggah dokumen persyaratan.
2. Petugas memverifikasi berkas dan mendisposisikan ke dinas teknis.
3. Dinas teknis melakukan peninjauan lapangan bila diperlukan.
4. Izin diterbitkan sebagai PDF bertanda tangan elektronik; warga dan dinas menerima notifikasi.
5. Retribusi dibayar lewat bank mitra; status pembayaran masuk lewat webhook.
6. Statistik layanan dilaporkan ke pimpinan daerah dan dipublikasikan di dasbor publik.

### P4 Pemangku kepentingan dan konflik tujuan

- Pimpinan daerah dan sekretariat: indeks kepuasan dan antrean MPP yang tidak mengular pada musim batas waktu.
- Dinas perizinan: permohonan selesai tepat waktu; dokumen persyaratan aman.
- Dinas pendapatan: pembayaran retribusi tercatat pada hari yang sama.
- Inspektorat dan petugas persandian: akses vendor terkendali, data pribadi warga tidak bocor, jejak audit tersedia.
- Dinas TIK: tim kecil, anggaran tetap, sangat bergantung pada vendor.
- Warga di daerah bersinyal lemah: halaman harus ringan dan unggahan tidak gagal di tengah jalan.
- Konflik utama: musim batas waktu menuntut kapasitas besar beberapa minggu dalam setahun, sedangkan anggaran tetap dan pengadaan lambat. Cloud publik menawarkan elastisitas, tetapi kebijakan kepala daerah mewajibkan data pribadi warga tetap di infrastruktur pemerintah.

### P5 Insiden pemicu

Menjelang batas perpanjangan izin reklame dan izin usaha 31 Januari, listrik di gedung Dinas TIK padam berulang; UPS hanya bertahan 20 menit dan disk server penuh oleh unggahan dokumen. Dalam dua hari portal tidak tersedia total 19 jam. Sebanyak 6.300 permohonan menumpuk, antrean MPP mengular hingga halaman parkir, dan pimpinan daerah memperpanjang batas waktu dua minggu.

### P6 Target 12 minggu

1. Infrastruktur portal didefinisikan sebagai kode dan dapat dibangun ulang dari repo di ruang server Dinas TIK maupun lokasi cadangan.
2. SLA 99,5% per bulan untuk portal dan API layanan, dengan p95 < 800 ms.
3. Akses vendor dan data pribadi warga terkendali dan dapat diaudit.
4. Biaya cloud publik tidak melampaui pagu APBD.
5. Informasi publik dan statistik layanan diterbitkan dari cloud publik agar lonjakan musiman tidak membebani server pemerintah.

## Tabel E — Arsitektur, lokasi, trafik, dan rencana

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | Portal web warga; API layanan; database permohonan; antrean dan worker untuk pembuatan PDF izin dan notifikasi SMS/email; analytics statistik layanan dan arsip; object storage dokumen persyaratan. Semua komponen kecuali notifikasi masih satu aplikasi buatan vendor. |
| E2 | Lokasi | Ruang server di gedung Dinas TIK di ibu kota kabupaten; MPP dan kompleks perkantoran perangkat daerah terhubung serat optik; kantor kecamatan terhubung VPN lewat internet; pusat data pemerintah provinsi (fiktif) tersedia sebagai lokasi cadangan dengan perjanjian kerja sama. |
| E3 | Pola trafik | 70% north-south (warga dan ASN ke portal, unggahan dokumen), 30% east-west (API ↔ database ↔ worker). Warga 78% mengakses dari jaringan seluler. |
| E4 | Ketersediaan | SLA 99,5% per bulan untuk portal dan API layanan; dasbor statistik best effort. |
| E5 | Latensi | p95 < 800 ms di sisi server untuk halaman dan API permohonan; unggahan diukur terpisah. |
| E6 | Kendala tim | Bidang aplikasi Dinas TIK 6 orang: 2 ASN infrastruktur, 3 programmer kontrak, 1 petugas persandian. Tidak ada DBA. Pengembangan aplikasi bergantung pada vendor dengan kontrak tahunan. |
| E7 | Jaringan sekarang | Satu segmen flat untuk semua server; satu firewall di tepi; vendor mengakses lewat SSH dari internet dengan daftar IP yang tidak pernah diperbarui. |
| E8 | Rencana migrasi | Hybrid wajib dalam 12 bulan: data pribadi warga, database permohonan, dan dokumen persyaratan tetap di infrastruktur pemerintah; informasi publik, dasbor statistik, dan arsip izin terbit (informasi publik) ke cloud publik region Jakarta. |

## Tabel S — Storage

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | Database permohonan relasional 820 GB; 1,6 juta permohonan sejak 2019; disk lokal satu server. |
| S2 | Dokumen bersama | Arsip surat keputusan dan nota dinas ±4,5 TB pada satu NAS; diakses 31 perangkat daerah lewat SMB. |
| S3 | Analytics | Log akses dan event perubahan status ±6 GB per hari; disimpan 2 tahun untuk evaluasi layanan. |
| S4 | Unggahan | Dokumen persyaratan (KTP, NPWP, gambar teknis) 38 TB, rata-rata 2,4 MB per berkas; pada Januari mencapai 45 ribu unggahan per hari. |
| S5 | Backup | Backup harian ke hard disk eksternal yang dibawa pulang staf setiap Jumat; hanya satu salinan; belum pernah diuji restore. |
| S6 | Insiden storage | Disk server penuh pada Januari sehingga unggahan gagal (P5). |
| S7 | Tim storage | 2 ASN infrastruktur; tidak ada DBA; belum pernah memakai object storage. |
| S8 | Rencana storage | Dokumen persyaratan ke object storage kompatibel S3 di ruang server pemerintah; database tetap on-premises dengan volume terpisah; arsip izin terbit ke cloud publik. |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Publik: daftar izin terbit, katalog layanan, statistik. Internal: disposisi, nota dinas. Rahasia: NIK, nomor KK, foto KTP, NPWP, alamat, dan data pemohon lainnya. |
| A2 | Regulasi dan kepatuhan | UU 27/2022 tentang Pelindungan Data Pribadi; PP 71/2019 tentang Penyelenggaraan Sistem dan Transaksi Elektronik untuk penyelenggara lingkup publik. Kebijakan kepala daerah dalam kasus: data pribadi warga hanya disimpan di infrastruktur milik pemerintah. Parameter kasus: arsip izin disimpan 10 tahun. |
| A3 | Ancaman utama | Deface dan banjir permintaan saat musim batas waktu; kebocoran NIK; akun operator kecamatan yang dipakai bersama. |
| A4 | Akses pihak ketiga | Vendor pengembang dengan kontrak tahunan dan akses SSH; bank mitra pembayaran retribusi lewat webhook; integrasi dengan sistem perizinan nasional. |
| A5 | Rahasia | Password database, kredensial gateway SMS, kunci privat sertifikat tanda tangan elektronik, passphrase state. |
| A6 | Insiden keamanan | Vendor lama yang kontraknya berakhir Desember masih memiliki akses SSH dan salinan database di laptop. Dokumen persyaratan dapat diunduh lewat URL bernomor urut tanpa login. |

## Tabel L — Aplikasi legacy

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | Aplikasi Cek Status Berkas versi 0.9: API kecil di satu server yang dibuat tangan oleh vendor lama. |
| L2 | Pengguna | Warga (rata-rata 2.400 pengecekan per hari, 18.000 per hari pada Januari); papan informasi digital di kantor kecamatan dan MPP yang alamatnya tertanam; chatbot pengaduan. |
| L3 | Jadwal pakai | Jam layanan Senin–Jumat 07.30–16.00 dan Sabtu 08.00–12.00 di MPP; malam dan Minggu sepi. |
| L4 | Toleransi downtime | Boleh berhenti hingga 2 jam di luar jam layanan (Sabtu siang sampai Minggu); di jam layanan jeda ≤ 10 detik. |
| L5 | Data | 1,2 GB status berkas dan riwayat; disinkronkan dari database utama setiap malam pukul 23.00. |

## Tabel O — Operasi dan observability

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Ketersediaan 99,5% per 30 hari (anggaran galat 216 menit); p95 < 800 ms; rasio galat ≤ 0,5%. Kesegaran: status berkas di papan informasi saat ini tertinggal hingga 1 hari; target baru ≤ 15 menit. |
| O2 | Jam sibuk | 08.00–11.00 hari kerja; musim Januari (perpanjangan izin) dan Agustus–September (pajak bumi dan bangunan). |
| O3 | Beban puncak | Normal 25 permintaan/detik; puncak 31 Januari 340 permintaan/detik (13,6 kali). |
| O4 | Alert yang diinginkan | Latensi dan galat di atas SLO; API mati; disk unggahan > 80%; worker PDF tertahan; drift. Pemanggilan di luar jam kerja hanya pada musim puncak. |
| O5 | Runbook dan insiden | Insiden P5 diketahui dari laporan petugas MPP; penanganan dengan menelepon vendor. Tidak ada runbook. |
| O6 | Pemegang on-call | Tidak ada on-call di luar jam kerja; selama musim puncak dua orang piket bergilir sampai pukul 22.00. |

## Tabel G — Tata kelola dan biaya

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-020 Dinas TIK (platform), CC-031 Perizinan, CC-045 Pendapatan Daerah, CC-060 Kecamatan. |
| G2 | Lingkungan | dev (dipakai vendor), staging, prod. |
| G3 | Anggaran bulanan | Pagu APBD cloud publik Rp 18 juta per bulan (Rp 216 juta per tahun), tidak dapat dinaikkan di tengah tahun; cadangan musiman maksimal Rp 9 juta pada Januari dan September. September lalu tagihan Rp 31 juta (72% di atas pagu) karena VM uji milik vendor tidak dimatikan. |
| G4 | Kebijakan label | owner, env, cost-center, data-class wajib; data-class rahasia hanya di prod dan hanya di infrastruktur pemerintah; resource milik vendor wajib berlabel owner vendor. |
| G5 | Pemasok cloud | Ruang server pemerintah (diperankan Koma Lab) dan cloud publik GCP region Jakarta lewat pengadaan tahunan; penyedia cloud publik dapat berganti setiap tahun anggaran. |
| G6 | Kekhawatiran lock-in | Kontrak tahunan membuat perpindahan penyedia nyata, bukan hipotetis; kode harus dapat diarahkan ke penyedia lain dengan perubahan minimum. |

## Tabel H — Hybrid dan integrasi

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Database permohonan, dokumen persyaratan, API layanan, dan layanan tanda tangan elektronik (A2, E8). |
| H2 | Integrasi antarsistem | Dasbor publik di cloud membutuhkan statistik harian layanan (agregat, tanpa data pribadi) dari API on-premises. |
| H3 | Pesan dan event | Setiap perubahan status permohonan menjadi event pada satu topik; konsumennya notifikasi warga dan statistik. |
| H4 | Arsip | Daftar izin terbit dan statistik harian diarsip ke cloud publik; retensi 10 tahun. Bucket lab menghapus objek setelah 7 hari. |
| H5 | Kebutuhan cloud publik | GCS region Jakarta untuk arsip informasi publik; Pub/Sub untuk event status; Cloud Run untuk portal informasi publik pada musim puncak. |
| H6 | Kegagalan dan aturan perubahan | Internet kantor memakai 1 ISP 200 Mbps dan putus rata-rata 3 kali per bulan (total ±5 jam). Operator vendor pernah mengubah izin bucket dasbor dari konsol sehingga dasbor publik kosong selama 2 hari. |

## Tabel C — Cloud-native dan skala

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API layanan (stateless); antrean pembuatan PDF izin dan notifikasi; worker. |
| C2 | Pola beban | Musiman dan dapat diprediksi dari kalender batas waktu; harian 08.00–11.00; malam dan akhir pekan sangat sepi. |
| C3 | Kebutuhan skala | API 25 → 340 permintaan/detik pada puncak; worker PDF harus menyelesaikan tumpukan 6.300 dokumen dalam satu hari kerja. Rencana 12 server aplikasi di ruang server dan lokasi cadangan. |
| C4 | Rilis bertahap | Rilis baru dicoba dulu pada satu jenis layanan (surat keterangan); tidak ada rilis dalam 2 minggu sebelum batas waktu. |
| C5 | Kuota | Cluster on-premises kecil dan dipakai bersama aplikasi pemerintah lain; kuota sama dengan lab. |
| C6 | Serverless | Portal informasi publik kandidat Cloud Run (sepi malam, lonjakan musiman); layanan yang menyentuh data pribadi tidak boleh di cloud publik. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di portal kabupaten |
|---|---|
| web | portal warga |
| API | API layanan; endpoint pesanan = permohonan layanan |
| database | database permohonan (S1) |
| worker dan antrean | pembuat PDF izin dan pengirim notifikasi |
| analytics dan arsip | statistik layanan, arsip izin terbit di GCS |
| object storage | dokumen persyaratan (S4) |
| aplikasi legacy M06 | Aplikasi Cek Status Berkas v0.9 |
| Pub/Sub dan Cloud Run | topik status permohonan; portal informasi publik |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil kelompok |
|---|---|---|
| M01 | P5, E1, E4, E6 | konvensi nama dan label yang membedakan milik vendor dan milik pemerintah; refaktor tanpa replace |
| M02 | E1, E6, C3 | container atau VM; pull atau push untuk 12 server dengan tim kecil; bake atau fry |
| M03 | E3, E7, A3, A4 | segmentasi tier; jalur SSH vendor; aturan east-west |
| M04 | S1–S8 | model akses per data; backup yang dibawa pulang; volume database dan unggahan |
| M05 | A1–A6 | temuan paling berbahaya; letak kunci tanda tangan elektronik; kebijakan yang menolak URL publik |
| M06 | L1–L5 | strategi per komponen; peralihan di luar jam layanan; kriteria contract |
| M07 | O1–O6 | ambang 0,8 s dan 0,5%; anggaran 216 menit dibandingkan 19 jam; pemanggilan di luar jam kerja |
| M08 | G1–G6, A1 | pusat biaya per perangkat daerah; rahasia hanya prod dan on-prem; broker untuk penyedia yang berganti |
| M09 | H1–H6 | apa yang boleh ke cloud publik; perilaku bila internet kantor putus; retensi 10 tahun |
| M10 | C1–C6 | pre-scale dari kalender atau autoscale; canary per jenis layanan; scale to zero untuk portal informasi |

## Alur babak M01–M10

### Babak 1 — M01: server milik siapa?

- Pemicu: setelah insiden P5, inventaris menemukan server yang dibuat vendor tanpa dokumentasi; tidak jelas mana milik pemerintah dan mana milik vendor.
- Tugas tim: membuat repo `koma-infra`, stack sandbox dengan layanan web dan api, label pemilik dan peran, ukuran dari katalog.
- Keputusan: konvensi label yang membedakan pemilik; `moved` agar server yang melayani tidak diganti.
- Benang data: inventaris sumber data (permohonan, unggahan, status, pembayaran; E1).
- Warisan: tag `m01`, konvensi label, `log-keputusan.md`.

### Babak 2 — M02: server yang bisa dipasang ulang tanpa vendor

- Pemicu: pemasangan server bergantung pada vendor; kontrak berakhir setiap Desember.
- Tugas tim: mengukur container dan VM, cloud-init, Ansible, image siap pakai.
- Keputusan: container atau VM per komponen; pull atau push untuk 12 server (C3) dengan 2 orang infrastruktur; bake atau fry.
- Benang data: server aplikasi tanpa data lokal; dokumen dan database dipisah di babak 4.
- Warisan: image dan konfigurasi server yang dimiliki pemerintah, bukan vendor.

### Babak 3 — M03: SSH vendor dari internet

- Pemicu: vendor mengakses semua server lewat SSH dari internet dalam satu segmen flat (E7, A4).
- Tugas tim: VPC tiga tier, ACL per tier, load balancer; stack jaringan terpisah.
- Keputusan: segmentasi untuk trafik 70% north-south; jalur administrasi; database hanya dari tier API.
- Benang data: jalur data pribadi warga dari portal ke database dibuat eksplisit.
- Warisan: pola stack jaringan dan ACL.

### Babak 4 — M04: disk penuh di bulan Januari

- Pemicu: unggahan gagal karena disk penuh (S6); backup dibawa pulang staf (S5).
- Tugas tim: state remote dengan lock, volume database terpisah, dokumen bersama, bucket dokumen persyaratan berversi.
- Keputusan: block/file/object untuk S1, S2, S4; ukuran volume; siapa membaca bucket state.
- Benang data: dokumen persyaratan sebagai object storage; kapasitas musiman Januari (45 ribu unggahan per hari).
- Warisan: bucket state dan pola volume terpisah.

### Babak 5 — M05: vendor lama dan URL bernomor urut

- Pemicu: vendor lama masih memegang akses dan salinan database; dokumen dapat diunduh lewat URL tebakan (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman, password baru, state terenkripsi, Trivy dan Conftest.
- Keputusan: temuan paling berbahaya; letak kunci tanda tangan elektronik; pencabutan akses vendor.
- Benang data: klasifikasi data pemohon (A1) menjadi aturan yang diuji otomatis.
- Warisan: kebijakan Conftest dan enkripsi state.

### Babak 6 — M06: cek status berkas tanpa mengganti papan informasi

- Pemicu: Aplikasi Cek Status Berkas v0.9 harus diganti sebelum Januari; papan informasi kecamatan memakai alamat tetap (L1, L2).
- Tugas tim: mengimpor legacy, membangun versi baru dengan volume terpisah, menyalin data, mengalihkan forward, membongkar legacy.
- Keputusan: strategi per komponen; peralihan di luar jam layanan; kriteria contract.
- Benang data: data status disalin dari sinkron malam; kesegaran data menjadi isu berikutnya.
- Warisan: API baru sebagai target monitoring M07.

### Babak 7 — M07: tahu sebelum antrean MPP mengular

- Pemicu: insiden P5 diketahui dari petugas MPP (O5).
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang 0,8 s dan 0,5%; `for:`; siapa menerima alert di luar jam kerja (O6).
- Benang data: kesegaran status berkas (dari 1 hari menuju 15 menit) sebagai SLO data.
- Warisan: aturan SLO untuk canary M10.

### Babak 8 — M08: tagihan 72% di atas pagu

- Pemicu: VM uji vendor tidak dimatikan dan tagihan September melampaui pagu (G3).
- Tugas tim: modul layanan-web, dev dan prod dari kode yang sama, label wajib, showback, broker Incus dan GCP.
- Keputusan: pemetaan pusat biaya perangkat daerah; aturan rahasia hanya prod dan on-prem; nilai broker ketika penyedia berganti tiap tahun (G6).
- Benang data: biaya data per perangkat daerah; label `data-class` mencegah data pemohon keluar.
- Warisan: modul dan kebijakan tata kelola untuk pipeline M09.

### Babak 9 — M09: dasbor publik yang kosong

- Pemicu: izin bucket dasbor diubah dari konsol dan dasbor kosong 2 hari (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip harian.
- Keputusan: data apa yang boleh keluar (agregat dan informasi publik); perilaku bila internet kantor putus; retensi 10 tahun dibandingkan lifecycle lab.
- Benang data: statistik harian sebagai pipeline hybrid; event status sebagai kanal notifikasi.
- Warisan: pipeline dan stack GCP untuk M10.

### Babak 10 — M10: menyiapkan Januari berikutnya

- Pemicu: kalender batas waktu Januari sudah diketahui; pimpinan meminta bukti portal tahan 340 permintaan/detik dan dapat dibangun ulang bila ruang server padam.
- Tugas tim: API, antrean, dan worker di cluster sebagai kode; HPA; canary; Cloud Run untuk portal informasi; rebuild dari namespace kosong.
- Keputusan: pre-scale berbasis kalender atau autoscale; canary per jenis layanan; cluster atau serverless.
- Benang data: antrean PDF memisahkan penerimaan permohonan dari penerbitan dokumen.
- Warisan: ADR akhir dan laporan arsitektur portal.
