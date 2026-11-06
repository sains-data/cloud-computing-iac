# Kasus k01 — Klinik Sehat Lampung

> Studi kasus simulasi pedagogis; bukan organisasi nyata. Semua nama, angka, insiden, dan kebijakan internal fiktif. Rujukan regulasi dipakai sebagai konteks kasus; tafsiran hukum tidak dinilai.

## Peran kelompok dalam cerita

Kelompok Anda adalah tim platform dan data engineering junior yang baru dibentuk di Divisi TI Klinik Sehat Lampung (KSL). Tim melapor kepada Kepala Platform dan bekerja bersama tim infrastruktur, DBA, dan Komite Rekam Medis. Selama 12 minggu tim membangun platform RME (rekam medis elektronik) dan data KSL sebagai kode di repo `koma-infra`, dari tag `m01` sampai `m10`. Kebijakan Divisi TI: semua lingkungan uji dibongkar setiap akhir pekan kerja dan harus dapat dibangun ulang dari repo. Karena itu, infrastruktur setiap modul dibongkar di akhir modul dan dibangun lagi dari kode.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

KSL adalah jaringan layanan kesehatan swasta dengan 64 klinik pratama, 6 klinik utama (dengan unit gawat darurat 24 jam), dan 2 laboratorium klinik rujukan, tersebar di 9 kabupaten/kota di Lampung dan 3 kota di Sumatera Selatan. KSL mempekerjakan 3.400 karyawan, termasuk 720 dokter dan dokter gigi serta 1.350 perawat, bidan, dan analis laboratorium. Pasien terdaftar berjumlah 1,26 juta orang dengan rata-rata 11.800 kunjungan per hari.

### P2 Model bisnis

Sekitar 58% kunjungan berasal dari peserta program jaminan kesehatan nasional dengan pembayaran kapitasi dan klaim; 42% berasal dari pasien umum dan 14 asuransi swasta mitra. KSL juga memegang kontrak medical check-up (MCU) dengan 230 perusahaan. Klaim yang terlambat atau ditolak karena data tidak lengkap langsung menahan arus kas; layanan yang berhenti di pagi hari langsung mengurangi kunjungan.

### P3 Proses bisnis utama

1. Pasien mendaftar lewat kios antrean di klinik, aplikasi pasien, atau loket.
2. Perawat melakukan triase; dokter membuka ringkasan rekam medis dan menulis pemeriksaan di RME.
3. Dokter membuat order laboratorium atau radiologi; laboratorium mengirim hasil (PDF dan nilai terstruktur) kembali ke RME.
4. Resep diteruskan ke farmasi klinik; tagihan dan klaim dibentuk dari data kunjungan.
5. Notifikasi hasil lab dan pengingat jadwal dikirim ke pasien.
6. Laporan mutu layanan dan laporan wajib ke dinas kesehatan disusun dari data agregat.

### P4 Pemangku kepentingan dan konflik tujuan

- Direktur Medis: RME harus tersedia 24 jam karena 6 klinik utama melayani gawat darurat.
- Komite Rekam Medis dan petugas pelindungan data: akses minimum, audit setiap pembukaan rekam medis, retensi panjang.
- Direktur Keuangan: klaim tepat waktu dan biaya TI dapat dipertanggungjawabkan per unit.
- Divisi TI (14 orang): banyak lokasi, tim kecil, belum terbiasa infrastruktur sebagai kode.
- Mitra (2 laboratorium eksternal, 14 asuransi, vendor kios antrean): butuh akses API yang stabil.
- Konflik utama: dokter ingin membuka riwayat pasien lintas klinik secepat mungkin, sedangkan Komite menuntut akses dibatasi pada hubungan perawatan. Keuangan ingin arsip pindah ke cloud publik yang murah, sedangkan Komite menolak data identitas pasien keluar dari pusat data milik KSL.

### P5 Insiden pemicu

Senin pukul 07.40, saat pendaftaran pagi mencapai puncak, RME berhenti selama 3 jam 10 menit (190 menit). Penyebabnya volume log transaksi database penuh; tidak ada alert, dan Divisi TI baru tahu setelah 23 klinik menelepon. Selama gangguan, 2.100 pasien dicatat di kertas dan datanya diinput ulang selama 3 hari. Dua minggu kemudian, audit internal menemukan 41 akun dokter yang sudah keluar masih aktif.

### P6 Target 12 minggu

Direksi memberi waktu 12 minggu untuk:

1. mendefinisikan seluruh infrastruktur RME dan data sebagai kode yang dapat dibangun ulang dalam ≤ 4 jam;
2. menjaga SLA 99,95% per bulan untuk API RME dan pendaftaran;
3. mendeteksi gangguan sebelum klinik menelepon (target ≤ 5 menit);
4. mencatat 100% akses ke rekam medis;
5. memindahkan arsip ter-pseudonim dan analytics ke cloud publik tanpa memindahkan identitas pasien.

## Tabel E — Arsitektur, lokasi, trafik, dan rencana

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | Portal web pasien dan dasbor klinik; API RME (pendaftaran, rekam medis, order lab); database relasional RME; antrean dan worker untuk pengiriman hasil lab, notifikasi, dan sinkronisasi klaim; layanan analytics mutu layanan dan arsip; object storage untuk hasil lab PDF, foto klinis, dan surat rujukan. Pendaftaran dan RME masih satu aplikasi besar; notifikasi sudah dipisah. |
| E2 | Lokasi | Kantor pusat dan pusat data primer di Bandar Lampung; ruang server sekunder di klinik utama Metro (jarak ±50 km); 70 klinik dan 2 laboratorium terhubung VPN site-to-site lewat broadband 20–50 Mbps dengan cadangan LTE. |
| E3 | Pola trafik | 35% north-south (klinik, pasien, mitra → API), 65% east-west (API ↔ database ↔ worker ↔ laboratorium). Rata-rata pembukaan satu rekam medis memicu 14 kueri ke database. |
| E4 | Ketersediaan | SLA 99,95% per bulan untuk API RME dan pendaftaran, 24 jam; portal pasien 99,5%; laporan analytics boleh tertunda hingga H+1. |
| E5 | Latensi | p95 API RME < 500 ms untuk membuka ringkasan rekam medis; laporan batch tidak sensitif latency. |
| E6 | Kendala tim | Divisi TI 14 orang: 4 infrastruktur dan jaringan, 2 DBA, 6 pengembang, 2 helpdesk; ditambah 1 petugas TI di setiap klinik utama. Belum ada yang memakai IaC; tim platform junior (kelompok) baru direkrut. |
| E7 | Jaringan sekarang | Setiap klinik memakai satu segmen flat /24. Di pusat data, web, API, database, dan server vendor berada dalam satu segmen server; firewall hanya di tepi internet dan VPN. |
| E8 | Rencana migrasi | Dalam 6 bulan, arsip ter-pseudonim dan analytics pindah ke cloud publik region Jakarta. Database dan API RME tetap di private cloud milik KSL minimal 3 tahun. Portal jadwal dokter (data publik) boleh di cloud publik. |

## Tabel S — Storage

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | Database RME relasional 6,8 TB, tumbuh 1,9 TB per tahun; disk lokal server primer di Bandar Lampung dengan replika asinkron ke Metro (lag rata-rata 40 detik). |
| S2 | Dokumen bersama | SOP klinis, formulir persetujuan tindakan, dan kontrak asuransi ±9 TB pada dua NAS (pusat dan Metro) lewat SMB; dibaca semua klinik. |
| S3 | Analytics | Log audit akses dan event kunjungan ±65 GB per hari; data mart mutu layanan 3,4 TB. Log audit disimpan 6 tahun. |
| S4 | Unggahan | Hasil lab PDF, foto klinis, dan rujukan hasil pindai ±150 TB, tumbuh 4 TB per bulan; tidak pernah diubah setelah ditandatangani dan tidak boleh tertimpa. |
| S5 | Backup | Backup penuh mingguan Minggu 01.00–07.00 dan inkremental harian ke NAS di ruangan yang sama dengan server; tape bulanan dibawa ke Metro. Restore penuh belum pernah diuji. |
| S6 | Insiden storage | Volume log transaksi database penuh dan RME berhenti 190 menit (P5). Setahun lalu restore 3.200 foto klinis gagal karena berkas backup korup. |
| S7 | Tim storage | 2 DBA dan 4 orang infrastruktur; belum pernah mengelola object storage kompatibel S3. |
| S8 | Rencana storage | Unggahan baru ke object storage kompatibel S3 di private cloud dengan versioning; volume database dipisah dari server; arsip ter-pseudonim ke GCS (E8). |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Publik: jadwal dokter, lokasi klinik. Internal: SOP, jadwal jaga, statistik agregat. Rahasia: identitas pasien, rekam medis, hasil lab, foto klinis, data klaim. Data ter-pseudonim tetap berlabel rahasia; hanya agregat tanpa identitas yang boleh berlabel internal. |
| A2 | Regulasi dan kepatuhan | Data kesehatan termasuk data pribadi yang bersifat spesifik menurut UU 27/2022 tentang Pelindungan Data Pribadi. Ketentuan rekam medis elektronik mewajibkan penyimpanan jangka panjang; parameter kasus: rekam medis disimpan 25 tahun sejak kunjungan terakhir. Kebijakan internal: identitas pasien tidak keluar dari pusat data KSL. Kontrak asuransi mewajibkan jejak audit akses. |
| A3 | Ancaman utama | Insider yang membuka rekam medis tanpa hubungan perawatan; akun bekas karyawan; ransomware dari PC klinik yang berada di segmen flat; tautan hasil lab yang dapat dibuka tanpa autentikasi. |
| A4 | Akses pihak ketiga | 2 laboratorium mitra mengirim hasil lewat API; 14 asuransi menarik data klaim; vendor kios antrean memiliki VPN permanen ke segmen server pusat. |
| A5 | Rahasia | Password database RME, 12 kunci API laboratorium mitra, sertifikat TLS, passphrase state. Kunci API vendor kios tertulis di berkas konfigurasi pada 140 kios. |
| A6 | Insiden keamanan | 41 akun dokter yang sudah keluar masih aktif (P5). Satu tautan hasil lab tanpa kedaluwarsa tersebar di grup percakapan pasien dan dapat dibuka siapa saja selama 11 hari. |

## Tabel L — Aplikasi legacy

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | Sistem Antrean Pendaftaran versi 0.9: API kecil di satu server yang dibuat tangan pada 2019 di pusat data; data antrean dan jadwal dokter di satu volume. |
| L2 | Pengguna | 140 kios antrean di 70 klinik; alamat API tertanam di firmware kios, dan pembaruan firmware butuh kunjungan teknisi (sekitar 3 bulan untuk semua klinik). Ditambah 380 petugas pendaftaran. |
| L3 | Jadwal pakai | 06.30–21.00 setiap hari di klinik pratama; 24 jam di 6 klinik utama. Paling sepi 00.00–05.00 (±40 pendaftaran per jam). |
| L4 | Toleransi downtime | Jeda ≤ 2 detik per peralihan; kios menampilkan galat setelah 3 detik dan pasien harus mengambil antrean ulang. Jendela pemeliharaan Selasa 01.00–04.00, maksimal 30 menit, dihitung dalam anggaran SLA 99,95%. |
| L5 | Data | 3,2 GB: nomor antrean 90 hari terakhir dan jadwal 720 dokter. Saat sibuk ada sekitar 35 pendaftaran baru per menit, sehingga selisih tulisan selama penyalinan harus ditangani. |

## Tabel O — Operasi dan observability

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Ketersediaan 99,95% per 30 hari (anggaran galat 21,6 menit); p95 < 500 ms; rasio galat ≤ 0,05%. Kesegaran: hasil lab tampil di RME paling lambat 10 menit setelah dikirim laboratorium. |
| O2 | Jam sibuk | 07.00–10.30 (pendaftaran pagi) dan 16.00–19.00 (praktik sore); Senin paling padat. |
| O3 | Beban puncak | Normal 90 permintaan/detik; puncak Senin 07.30–08.30 sebesar 420 permintaan/detik; malam 12 permintaan/detik. |
| O4 | Alert yang diinginkan | Latensi p95 di atas target; galat di atas 0,05%; API mati; pemakaian volume database > 80%; antrean hasil lab tertahan > 10 menit; drift. Pemanggilan malam hanya untuk alert yang berdampak ke pasien. |
| O5 | Runbook dan insiden | Insiden P5 diketahui dari telepon klinik setelah 25 menit. Saat itu operator menambah ruang disk langsung di server tanpa catatan. Belum ada runbook tertulis. |
| O6 | Pemegang on-call | 4 orang infrastruktur dan 2 DBA bergiliran; satu orang on-call malam karena klinik utama buka 24 jam. |

## Tabel G — Tata kelola dan biaya

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-110 Layanan Klinis (RME), CC-120 Laboratorium, CC-210 Keuangan dan Klaim, CC-310 Analytics dan Mutu, CC-900 Platform TI bersama. |
| G2 | Lingkungan | dev, staging (uji integrasi dengan laboratorium mitra memakai data sintetis), prod. Dev dan staging tidak boleh berisi data pasien asli. |
| G3 | Anggaran bulanan | Anggaran operasional infrastruktur TI Rp 210 juta per bulan; porsi cloud publik maksimal Rp 35 juta. Tagihan uji coba cloud publik bulan lalu naik 55% (Rp 22 juta menjadi Rp 34,1 juta) tanpa pemilik yang jelas. |
| G4 | Kebijakan label | owner, env, cost-center, data-class wajib pada setiap resource. data-class rahasia hanya di prod dan hanya di private cloud. Ukuran prod minimal sedang. |
| G5 | Pemasok cloud | Private cloud di pusat data KSL (diperankan Koma Lab) dan satu cloud publik (GCP region Jakarta). Showback memakai tarif internal Divisi TI. |
| G6 | Kekhawatiran lock-in | Arsip 25 tahun tidak boleh terkunci pada format atau penyedia tertentu; biaya egress untuk mengambil kembali arsip harus diketahui sejak awal. |

## Tabel H — Hybrid dan integrasi

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Database RME, API RME, master pasien, dan object storage hasil lab tetap di private cloud (A2, E8). |
| H2 | Integrasi antarsistem | Tim analytics di cloud membutuhkan laporan harian mutu layanan per klinik (agregat, ter-pseudonim) dari API on-premises. |
| H3 | Pesan dan event | Event "hasil lab siap" dan "order lab dibuat" diterbitkan ke satu topik; konsumennya layanan notifikasi pasien dan analytics. |
| H4 | Arsip | Ringkasan harian ter-pseudonim diarsip ke cloud publik; retensi bisnis 10 tahun. Bucket lab menghapus objek setelah 7 hari karena alasan biaya sandbox. |
| H5 | Kebutuhan cloud publik | GCS region Jakarta untuk arsip dan analytics; Pub/Sub untuk distribusi event hasil lab; Cloud Run untuk portal jadwal dokter publik. |
| H6 | Kegagalan dan aturan perubahan | Pusat data memakai 2 ISP. Bila cloud publik tidak terjangkau 1 hari, RME harus tetap berjalan; laporan ke dinas boleh terlambat paling lama 3 hari. Seorang engineer pernah mengganti lifecycle bucket arsip uji dari konsol sehingga 9 hari arsip terhapus. |

## Tabel C — Cloud-native dan skala

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API pendaftaran dan jadwal (stateless) dipisah dari inti RME; antrean pengiriman notifikasi dan hasil lab; worker pengirim notifikasi. |
| C2 | Pola beban | Puncak pagi tajam setiap hari (4,7 kali beban normal pada Senin pagi); musim MCU korporat Februari–Maret dengan ±2.000 peserta per hari; pengingat jadwal dikirim serentak pukul 18.00. |
| C3 | Kebutuhan skala | API pendaftaran 90 → 420 permintaan/detik; worker notifikasi 30.000 pesan per jam saat pengingat jadwal. Rencana 24 server API RME dan 70 server cache di klinik. |
| C4 | Rilis bertahap | Fitur baru dirilis dulu di 2 klinik percontohan (sekitar 5% trafik), di luar jam sibuk pagi. |
| C5 | Kuota | Cluster platform dibagi lima tim; namespace tim platform memakai kuota yang sama dengan lab. |
| C6 | Serverless | Portal jadwal dokter publik boleh di Cloud Run; API yang menyentuh rekam medis tidak boleh di serverless publik. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di KSL |
|---|---|
| web | portal pasien dan dasbor klinik |
| API | API pendaftaran dan RME; endpoint pesanan = order laboratorium |
| database | database RME (S1) |
| worker dan antrean | pengirim hasil lab dan notifikasi pasien |
| analytics dan arsip | laporan mutu layanan ter-pseudonim, arsip di GCS |
| object storage | hasil lab PDF dan foto klinis (S4) |
| aplikasi legacy M06 | Sistem Antrean Pendaftaran v0.9 |
| Pub/Sub dan Cloud Run | topik hasil lab; portal jadwal dokter publik |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil kelompok |
|---|---|---|
| M01 | P5, E1, E4, E5 | konvensi nama dan label; refaktor tanpa replace pada server yang melayani SLA 99,95% |
| M02 | E1, E2, E6, C3 | container atau VM untuk RME, pendaftaran, database, analytics; pull atau push untuk 24 server API dan 70 server klinik di jaringan VPN yang tidak stabil |
| M03 | E3, E7, A3, A4 | segmentasi tier; posisi vendor kios; aturan east-west untuk 65% trafik |
| M04 | S1–S8 | model akses per data; volume database dengan batas ukuran; versioning hasil lab; siapa membaca state |
| M05 | A1–A6 | temuan paling berbahaya untuk data kesehatan; rotasi kunci; kebijakan yang menolak akses publik |
| M06 | L1–L5 | strategi per komponen; store and load dengan 35 tulisan per menit; jeda 2 detik terhadap anggaran 21,6 menit |
| M07 | O1–O6 | ambang 0,5 s dan 0,05%; `for:` yang muat dalam anggaran 21,6 menit; alert kesegaran hasil lab |
| M08 | G1–G6, A1 | pusat biaya per lingkungan; aturan rahasia hanya prod dan hanya private cloud; kriteria broker |
| M09 | H1–H6 | apa yang boleh keluar ke GCP; perilaku saat cloud putus; retensi arsip 10 tahun dibandingkan lifecycle lab |
| M10 | C1–C6, O1 | komponen yang boleh ke cluster atau serverless; canary di 2 klinik; skala pengingat jadwal |

## Alur babak M01–M10

### Babak 1 — M01: inventaris setelah Senin kelabu

- Pemicu: audit pasca-insiden P5 menemukan dua server uji integrasi laboratorium yang dibuat tangan; tidak ada yang tahu mana yang dipakai laboratorium mitra.
- Tugas tim: membuat repo `koma-infra`, stack sandbox dengan layanan web dan api, label pemilik, dan ukuran dari katalog.
- Keputusan: konvensi nama dan label yang dapat dibaca auditor; `moved` untuk refaktor karena server yang melayani RME tidak boleh diganti (E4 99,95%).
- Benang data: inventaris sumber data (pendaftaran, RME, hasil lab, klaim; E1) dimulai dari label peran.
- Warisan: tag `m01`, konvensi label, dan `log-keputusan.md` yang dipakai semua babak.

### Babak 2 — M02: server API yang tidak dipasang tangan

- Pemicu: Divisi TI berencana menambah 24 server API RME dan 70 server cache di klinik (C3); pemasangan manual memakan dua hari per server.
- Tugas tim: mengukur container dan VM, memasang API dengan cloud-init dan Ansible, memanggang image.
- Keputusan: container atau VM untuk empat komponen E1; pull atau push untuk server di klinik yang terhubung VPN tidak stabil (E2); bake atau fry.
- Benang data: server API sengaja tanpa data yang harus selamat; data RME dipisahkan di babak 4.
- Warisan: image dan konfigurasi server API yang dipakai ulang di M06–M10.

### Babak 3 — M03: vendor kios tidak boleh melihat database

- Pemicu: pemindaian internal menunjukkan server vendor kios di segmen yang sama dapat membuka port database RME (A3, A4, E7).
- Tugas tim: VPC tiga tier, ACL per tier, load balancer di depan web; stack jaringan terpisah dari stack aplikasi.
- Keputusan: matriks konektivitas untuk 65% trafik east-west (E3); di mana vendor kios ditempatkan; egress yang masih terbuka.
- Benang data: database hanya menerima koneksi dari tier API; jalur data rekam medis menjadi eksplisit dan dapat diaudit.
- Warisan: pola stack jaringan dan ACL per tier.

### Babak 4 — M04: log penuh tidak boleh menghentikan RME lagi

- Pemicu: insiden 190 menit (S6) dan hasil lab yang tidak boleh tertimpa (S4).
- Tugas tim: state remote dengan lock, volume database terpisah berbatas ukuran, dokumen bersama SOP untuk dua server aplikasi, bucket hasil lab berversi.
- Keputusan: block/file/object untuk S1, S2, S4; ukuran volume dan ambang peringatan; siapa boleh membaca bucket state.
- Benang data: pemisahan penyimpanan RME, dokumen, dan objek; versioning sebagai jaminan integritas hasil lab.
- Warisan: bucket state kelompok dan pola volume terpisah.

### Babak 5 — M05: tautan hasil lab yang tersebar

- Pemicu: tautan hasil lab terbuka selama 11 hari dan 41 akun dokter masih aktif (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman, membangkitkan password baru, mengenkripsi state, memasang Trivy dan Conftest.
- Keputusan: temuan paling berbahaya bagi data kesehatan; rotasi kunci API laboratorium; aturan yang menahan bucket publik.
- Benang data: klasifikasi data (A1) diterjemahkan menjadi kebijakan yang dapat diuji.
- Warisan: kebijakan Conftest dan enkripsi state yang dipakai pipeline M09.

### Babak 6 — M06: antrean baru tanpa mengganti firmware kios

- Pemicu: Sistem Antrean v0.9 harus diganti versi 2.0, tetapi 140 kios memakai alamat tetap (L1, L2).
- Tugas tim: mengimpor legacy ke kode, membangun versi baru dengan volume terpisah, menyalin data, mengalihkan forward, membongkar legacy.
- Keputusan: strategi per komponen (antrean, RME, database, analytics); waktu peralihan di jendela Selasa 01.00–04.00; kriteria contract.
- Benang data: migrasi data antrean yang terus ditulis 35 kali per menit saat sibuk (L5).
- Warisan: API baru dari kode sebagai target monitoring M07.

### Babak 7 — M07: tahu sebelum 23 klinik menelepon

- Pemicu: insiden P5 diketahui setelah 25 menit (O5), lebih lama dari anggaran galat sebulan.
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang 0,5 s dan 0,05%; `for:` yang realistis terhadap anggaran 21,6 menit; alert kesegaran hasil lab.
- Benang data: kesegaran data (hasil lab ≤ 10 menit) diperlakukan sebagai SLO.
- Warisan: aturan SLO untuk menilai canary di M10.

### Babak 8 — M08: data pasien di lingkungan dev

- Pemicu: pengembang menyalin 1,2 juta baris data pasien ke VM dev untuk menguji fitur rujukan, dan tagihan uji coba naik 55% (G3).
- Tugas tim: modul layanan-web, lingkungan dev dan prod dari kode yang sama, label wajib, showback, broker Incus dan GCP.
- Keputusan: pemetaan pusat biaya ke lingkungan; aturan rahasia hanya di prod dan hanya di private cloud; beban mana yang boleh ke GCP.
- Benang data: label `data-class` sebagai metadata tata kelola data; biaya data per pusat biaya.
- Warisan: modul dan kebijakan tata kelola untuk pipeline M09.

### Babak 9 — M09: arsip ke cloud, identitas tetap di rumah

- Pemicu: rencana E8 berjalan; lifecycle bucket arsip uji pernah diubah dari konsol sehingga 9 hari arsip hilang (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, membuat bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip harian.
- Keputusan: isi laporan harian yang boleh keluar (agregat, ter-pseudonim); perilaku bila GCP putus; perbedaan retensi 10 tahun dan lifecycle lab.
- Benang data: pipeline data hybrid dan event hasil lab sebagai kanal (H2–H4).
- Warisan: pipeline dan stack GCP dipakai ulang di M10.

### Babak 10 — M10: musim MCU dan rebuild dari nol

- Pemicu: musim MCU korporat dan pengingat jadwal pukul 18.00 menekan API pendaftaran dan worker notifikasi (C2, C3).
- Tugas tim: API, antrean, dan worker di cluster sebagai kode; HPA; canary; Cloud Run untuk portal jadwal; rebuild dari namespace kosong.
- Keputusan: cluster atau serverless per komponen (C6); kriteria promosi canary di 2 klinik; apa yang tidak ikut dibangun ulang dan artinya bagi RTO.
- Benang data: antrean memisahkan pendaftaran dari pengiriman notifikasi; pesan yang belum diproses ikut hilang bila antrean tidak persisten.
- Warisan: ADR akhir dan laporan arsitektur platform RME.
