# Kasus k00 — Sumatera Data (contoh kerja dosen)

> Studi kasus simulasi pedagogis; bukan organisasi nyata. Semua nama, angka, dan insiden fiktif.

> **Status berkas.** Kasus ini adalah contoh kerja dosen yang dipakai di naskah Modul 01–10. Kasus ini tidak dibagikan kepada kelompok k01–k05. Fakta yang sudah dipakai naskah ditulis apa adanya beserta sumbernya dalam kurung, misalnya (P4 E3) untuk Pertemuan 4 kode E3 atau (M06) untuk naskah Modul 06. Fakta yang belum ada di naskah ditandai **(baru)**; fakta itu disusun agar konsisten dengan angka yang sudah dipakai dan boleh dipakai dosen saat membahas contoh. Slide Pertemuan 4–5 masih memakai nama lama "Nusa Data" untuk kasus yang sama.

## Peran kelompok dalam cerita

Di naskah, pembaca berperan sebagai anggota tim kecil Sumatera Data yang mengganti cara kerja manual dengan infrastruktur sebagai kode. Pada kasus k01–k05, peran yang setara adalah tim platform dan data engineering junior. Repo `koma-infra` tumbuh dari tag `m01` sampai `m10`; setiap akhir modul infrastruktur dibongkar dan dibangun ulang dari kode pada modul berikutnya.

## P — Profil dan konteks bisnis

### P1 Profil organisasi

Sumatera Data adalah perusahaan layanan data dan transaksi yang menjalankan aplikasi web, API, database, dan layanan analytics (M01). **(baru)** Perusahaan menyediakan platform pencatatan pesanan, kasir, dan laporan bagi sekitar 1.800 gerai ritel dan 46 distributor mitra di Sumatera, dengan 620 karyawan. Tim TI berjumlah 12 orang: 3 orang jaringan (P4 E6), 1 DBA (P5 S7), 6 pengembang aplikasi termasuk tim mobile, dan 2 analis data. Naskah menyebut tim ini "tim kecil" (M01); skala bisnisnya besar, tetapi unit TI-nya ramping.

### P2 Model bisnis

**(baru)** Pendapatan berasal dari biaya langganan per gerai (paket bulanan) dan biaya per transaksi yang diproses API. Pelanggan distributor membayar tambahan untuk laporan harian. Karena itu, gangguan API transaksi langsung mengurangi pendapatan, sedangkan keterlambatan laporan analytics masih dapat ditoleransi (P4 E4).

### P3 Proses bisnis utama

1. Gerai mencatat pesanan dan transaksi kasir lewat aplikasi mobile dan web (M06: aplikasi mobile memakai alamat publik yang tetap).
2. API transaksi menyimpan transaksi ke database relasional (P5 S1).
3. Pesanan diteruskan ke pemrosesan lanjutan lewat antrean dan worker (M10).
4. API laporan menyusun laporan pelanggan; laporan harian dikirim ke tim analytics (M05, M09).
5. Tim analytics memakai event klik untuk pelatihan model (P5 S3).
6. **(baru)** Gudang distribusi memakai aplikasi absensi untuk 20 staf internal (M06, contoh analog).

### P4 Pemangku kepentingan dan konflik tujuan

- Direksi: menuntut biaya cloud yang dapat ditelusuri ke pemakainya (M08) dan melarang perubahan infrastruktur di luar pipeline (M09).
- Tim aplikasi mobile: alamat publik API tidak boleh berubah karena aplikasi mobile tidak bisa diperbarui serentak (M06).
- Tim analytics: membutuhkan laporan harian dari API on-premises dan pindah ke cloud publik (M09, P4 E8).
- Tim jaringan (3 orang) dan DBA: kapasitas terbatas, tanpa pengalaman controller SDN dan Fibre Channel (P4 E6, P5 S7).
- Audit internal: menemukan laporan pelanggan dapat diunduh siapa saja yang tahu alamat bucket (M05).
- Konflik utama: kecepatan rilis API baru dan promo akhir tahun (M06, M10) berhadapan dengan SLA 99,9% dan kemampuan tim kecil.

### P5 Insiden pemicu

Server uji coba API dibuat dengan mengetik perintah satu per satu oleh orang yang sudah pindah tim. Ketika server rusak, tidak ada yang tahu ukuran memorinya, image yang dipakai, atau mengapa ada dua server bernama mirip, `sd-api-uji` dan `sd-api-uji2` (M01). Insiden berikutnya terjadi berurutan dan menjadi babak tiap modul (lihat Alur Babak).

### P6 Target 12 minggu

**(baru)** Dalam 12 minggu seluruh infrastruktur API transaksi, data, monitoring, tata kelola, dan integrasi cloud publik dapat dibangun ulang dari repo lewat pipeline, dengan bukti dapat diverifikasi. Target terukur: SLA 99,9% API transaksi terjaga (P4 E4), p95 < 300 ms (P4 E5), setiap rupiah biaya bertuan (M08), dan sistem dapat dibangun ulang dari namespace kosong dalam hitungan menit (M10).

## Tabel E — Arsitektur, lokasi, trafik, dan rencana (Pertemuan 4)

**Tabel 1 — Evidence Pack E1–E8**

| Kode | Butir | Fakta |
|---|---|---|
| E1 | Arsitektur aplikasi | web app + API + database + analytics service; sebagian sudah dipecah menjadi service (P4). **(baru)** Pesanan diproses worker lewat antrean (dipakai M10). |
| E2 | Lokasi | 1 kantor pusat, 3 kantor cabang, 1 private data center (P4). Kantor Medan dan Pekanbaru disebut di M09. **(baru)** Kantor pusat di Medan; cabang di Pekanbaru, Padang, dan Jambi. |
| E3 | Pola trafik | 22% north-south (pengguna → API), 78% east-west (API ↔ DB ↔ analytics) (P4) |
| E4 | Ketersediaan | SLA 99,9% untuk API transaksi; laporan analytics boleh tertunda (P4). Angka ilustrasi M02: server API dan server database masing-masing dijamin 99,95%, gabungan ≈ 99,90%. |
| E5 | Latensi | p95 API < 300 ms; batch analytics tidak sensitif latency (P4) |
| E6 | Kendala tim | tim jaringan 3 orang, tanpa pengalaman controller SDN (P4) |
| E7 | Jaringan sekarang | flat di kantor cabang, hierarchical 3-layer di data center, VLAN + STP (P4) |
| E8 | Rencana migrasi | analytics + object storage pindah ke cloud dalam 9 bulan; database tetap on-premises 2 tahun (P4) |

## Tabel S — Storage (Pertemuan 5)

**Tabel 2 — Evidence Pack S1–S8**

| Kode | Butir | Fakta |
|---|---|---|
| S1 | Data transaksi | relasional, 1,2 TB, di disk lokal dua server pada private data center (P5) |
| S2 | Dokumen bersama | kontrak dan laporan ±3 TB pada satu NAS; diakses kantor pusat dan 3 cabang (NFS dan SMB/CIFS) (P5) |
| S3 | Analytics | event klik JSON ±40 GB/hari; disimpan 2 tahun untuk pelatihan model (P5) |
| S4 | Unggahan | foto dan dokumen pelanggan ±6 TB; hampir tidak pernah diubah; diambil lewat aplikasi web (P5) |
| S5 | Backup | backup penuh malam hari 23.00–03.00 ke NAS yang sama, lewat LAN 1 Gbps yang juga dipakai pengguna (P5) |
| S6 | Insiden storage | akses file lambat pada jam backup; 2 kali setahun disk database penuh dan API berhenti (P5) |
| S7 | Tim storage | 3 orang jaringan (E6) + 1 DBA; tidak ada yang berpengalaman Fibre Channel (P5) |
| S8 | Rencana storage | analytics dan object storage ke cloud dalam 9 bulan; database tetap on-premises 2 tahun (= E8) (P5) |

## Tabel A — Keamanan

**Tabel 3 — Evidence Pack A1–A6**

| Kode | Butir | Fakta |
|---|---|---|
| A1 | Kelas data | Laporan pelanggan dan data transaksi pelanggan bersifat rahasia (M05, M06). Label `data-class` memakai publik/internal/rahasia; dev berlabel internal, prod berlabel rahasia (M08). **(baru)** Katalog produk gerai bersifat publik; laporan kinerja internal bersifat internal. |
| A2 | Regulasi dan kepatuhan | **(baru)** Data pribadi pemilik gerai dan pelanggan tunduk pada UU 27/2022 tentang Pelindungan Data Pribadi; kontrak dengan distributor mensyaratkan laporan hanya dapat diakses distributor yang bersangkutan. |
| A3 | Ancaman utama | Server web yang disusupi dapat langsung membuka koneksi ke database (M03); bucket laporan dapat diunduh siapa saja yang tahu alamatnya; mantan kontraktor masih memegang salinan repo beserta kredensial (M05). |
| A4 | Akses pihak ketiga | Seorang kontraktor menyerahkan stack API laporan lalu kontraknya selesai (M05). **(baru)** Distributor mengunduh laporan lewat API laporan dengan akun per distributor. |
| A5 | Rahasia | Password database tertulis literal di repo (M05); password lama harus dianggap bocor dan diganti. Passphrase enkripsi state hanya di lingkungan operator (M05). |
| A6 | Insiden keamanan | Audit internal menemukan laporan pelanggan dapat diunduh siapa saja yang tahu alamat bucket dan password database tercantum di repo (M05). Server berukuran besar di lingkungan pengembangan menyimpan salinan data pelanggan (M08). |

## Tabel L — Aplikasi legacy (Modul 06)

**Tabel 4 — Evidence Pack L1–L5**

| Kode | Butir | Fakta |
|---|---|---|
| L1 | Aplikasi | API transaksi lama versi 0.9 di server yang dibuat tangan dua tahun lalu oleh orang yang sudah tidak ada di tim (M06) |
| L2 | Pengguna | Aplikasi mobile yang memakai alamat publik tetap dan tidak bisa diperbarui serentak (M06). **(baru)** Sekitar 2.300 perangkat gerai aktif harian. |
| L3 | Jadwal pakai | **(baru)** 06.00–23.00 WIB setiap hari, mengikuti jam buka gerai; sepi pukul 23.00–06.00. |
| L4 | Toleransi downtime | Pengguna yang terus mengakses alamat publik selama peralihan hanya boleh mengalami jeda di bawah lima detik (M06); SLA 99,9% (anggaran 43,2 menit per 30 hari). |
| L5 | Data | Data di satu volume yang harus selamat sampai versi baru; dipindah dengan store and load (M06). Contoh analog lain: aplikasi absensi gudang di satu server, 20 staf internal, terhubung mesin sidik jari lokal, tanpa data sensitif → rehost (M06). |

## Tabel O — Operasi dan observability (Modul 07)

**Tabel 5 — Evidence Pack O1–O6**

| Kode | Butir | Fakta |
|---|---|---|
| O1 | SLO | Latensi: p95 < 300 ms (E5), SLI p95 jendela 5 menit. Ketersediaan: SLA 99,9% (E4), ambang galat 0,1% (M07). Anggaran galat 43,2 menit per 30 hari. |
| O2 | Jam sibuk | **(baru)** 11.00–14.00 dan 18.00–21.00 WIB; Sabtu malam paling ramai. |
| O3 | Beban puncak | **(baru)** Sekitar 120 permintaan/detik pada jam sibuk biasa dan 300 permintaan/detik pada Sabtu malam di API transaksi. |
| O4 | Alert yang diinginkan | Latensi tinggi: p95 > 0,3 s selama 2 menit; galat tinggi: > 0,1% selama 5 menit; API mati: `up == 0` selama 1 menit; drift: `iac_drift == 1` (M07, Tabel 7.7). |
| O5 | Runbook dan insiden | API melambat selama 40 menit dan baru diketahui ketika pelanggan mengeluh; operator menaikkan memori server API langsung di konsol, lalu apply berikutnya diam-diam mengembalikannya (M07). **(baru)** Belum ada runbook tertulis. |
| O6 | Pemegang on-call | **(baru)** Dua dari enam pengembang bergiliran mingguan; tim jaringan tidak memegang on-call aplikasi. |

## Tabel G — Tata kelola dan biaya (Modul 08)

**Tabel 6 — Evidence Pack G1–G6**

| Kode | Butir | Fakta |
|---|---|---|
| G1 | Pusat biaya | CC-101 (dev), CC-201 (prod) (M08); CC-305 untuk tim analytics di lingkungan staging hipotetis (M08 contoh kerja). |
| G2 | Lingkungan | dev: 1 web ukuran kecil; prod: 2 web ukuran sedang; kode sama, state terpisah (M08). |
| G3 | Anggaran bulanan | Tagihan cloud bulan lalu naik 40% tanpa ada yang bisa menjelaskan pemakainya (M08). Showback contoh: dev IDR 317.550, prod IDR 657.000, total IDR 974.550 per bulan pada skala lab (kunci M08). **(baru)** Anggaran infrastruktur cloud perusahaan Rp 60 juta per bulan. |
| G4 | Kebijakan label | owner, env, cost-center berbentuk CC-123, data-class publik/internal/rahasia; data rahasia hanya di prod; prod tidak boleh ukuran kecil (M08). |
| G5 | Pemasok cloud | private data center (diperankan Koma Lab/Incus) dan cloud publik GCP; tarif showback internal IDR 420 per vCPU-jam, IDR 60 per GiB-jam, 730 jam per bulan (M08). |
| G6 | Kekhawatiran lock-in | Direksi meminta opsi memindahkan beban ke penyedia lain tanpa menulis ulang semuanya (M08); beban analytics menjadi kandidat pemilihan Incus atau GCP. |

## Tabel H — Hybrid dan integrasi (Modul 09)

**Tabel 7 — Evidence Pack H1–H6**

| Kode | Butir | Fakta |
|---|---|---|
| H1 | Sistem tetap on-premises | Database transaksi dan API transaksi (E8: database tetap on-premises 2 tahun) (M09). |
| H2 | Integrasi antarsistem | Tim analytics di cloud membutuhkan laporan harian dari API on-premises (M09). |
| H3 | Pesan dan event | Aplikasi on-premises harus tahu ke topik mana pesanan dikirim (M09); topik dipakai pemrosesan pesanan (M10). |
| H4 | Arsip | Laporan harian dikirim ke bucket arsip di cloud publik (M09). **(baru)** Kebutuhan bisnis retensi laporan 2 tahun, selaras dengan S3; bucket lab menghapus objek setelah 7 hari karena alasan biaya sandbox. |
| H5 | Kebutuhan cloud publik | Object storage dan analytics pindah ke cloud publik (E8); GCS untuk arsip, Pub/Sub untuk topik pesanan, Cloud Run untuk API serverless (M09–M10). |
| H6 | Kegagalan dan aturan perubahan | Seorang engineer di kantor Pekanbaru mengganti nama bucket arsip dari konsol pada Jumat sore; laporan malam itu gagal dan baru disadari Senin. Engineer lain salah ketik satu huruf nama topik saat menyalin dari obrolan. Direksi menetapkan: tidak ada perubahan infrastruktur di luar pipeline (M09). |

## Tabel C — Cloud-native dan skala (Modul 10)

**Tabel 8 — Evidence Pack C1–C6**

| Kode | Butir | Fakta |
|---|---|---|
| C1 | Komponen yang dipecah | API stateless sebagai producer, Redis sebagai broker antrean pesanan, worker sebagai consumer (M10). |
| C2 | Pola beban | Promo akhir tahun diperkirakan melipatgandakan pesanan (M10). **(baru)** Lonjakan terkonsentrasi pada 25–31 Desember pukul 18.00–22.00. |
| C3 | Kebutuhan skala | API harus menskala sendiri (M10). Rencana mengelola 40 server API (M02). **(baru)** Perkiraan puncak promo 2,5 kali beban Sabtu malam (O3), sekitar 750 permintaan/detik. |
| C4 | Rilis bertahap | Versi baru dicoba pada sebagian pengguna lebih dulu (canary) (M10). |
| C5 | Kuota | Kuota namespace lab membatasi `limits.cpu` 2 CPU, sehingga HPA maksimum 4 Pod stabil dan canary 1 Pod (M10). |
| C6 | Serverless | Direksi bertanya: perlukah cluster sendiri, atau cukup serverless (M10)? Seluruh sistem harus dapat dibangun ulang dari repo dalam hitungan menit bila cluster hilang. |

## Pemetaan ke aplikasi contoh

| Komponen aplikasi contoh | Wujud di Sumatera Data |
|---|---|
| web | aplikasi web gerai dan laporan |
| API | API transaksi; endpoint pesanan = pesanan gerai |
| database | database transaksi (S1) |
| worker dan antrean | pemroses pesanan (M10) |
| analytics dan arsip | laporan harian ke tim analytics, arsip di GCS (M09) |
| object storage | unggahan pelanggan (S4), laporan pelanggan (M05) |
| aplikasi legacy M06 | API transaksi lama v0.9 |
| Pub/Sub dan Cloud Run | topik pesanan; API serverless pembanding cluster |

## Peta ke modul

| Modul | Kode bukti | Keputusan yang harus diambil |
|---|---|---|
| M01 | P5, E1, E4, E5 | konvensi nama dan label; layanan web dan api sebagai `for_each`; refaktor dengan `moved` tanpa replace server yang melayani transaksi |
| M02 | E1, E4, C3 | container atau VM untuk web, API, database, analytics; pull atau push untuk 40 server API; bake atau fry |
| M03 | E1, E3, E5, E7, A3 | segmentasi tiga tier, aturan east-west eksplisit, load balancer L4 |
| M04 | S1–S8 | model akses block/file/object per data; volume database terpisah; versioning unggahan; state remote |
| M05 | A1–A6 | temuan paling berbahaya; letak rahasia; pagar Trivy dan Conftest |
| M06 | L1–L5, E8 | strategi per komponen; store and load; blue-green dengan forward; kriteria contract |
| M07 | O1–O6, E4, E5 | ambang dan `for:` alert; anggaran galat 43,2 menit dibandingkan insiden 40 menit; penanganan drift |
| M08 | G1–G6, A1 | lingkungan dev/prod, label wajib, showback, kriteria broker untuk beban analytics |
| M09 | H1–H6, E8 | pemecahan stack, arsip laporan harian, topik pesanan, perilaku bila GCP putus, aturan hanya lewat pipeline |
| M10 | C1–C6, O1 | cluster atau serverless, canary, HPA di bawah kuota, rebuild dari nol |

## Alur babak M01–M10

Setiap babak meringkas cerita di naskah. Setiap akhir modul infrastruktur dibongkar; ini disiplin perusahaan, bukan putusnya cerita: apa pun yang tidak bisa dibangun ulang dari repo dianggap belum selesai.

### Babak 1 — M01: dari server uji coba ke stack yang dapat dibaca

- Pemicu: server `sd-api-uji` dan `sd-api-uji2` tidak bisa dijelaskan siapa pun (P5).
- Tugas tim: menulis stack sandbox dengan konvensi nama, label pemilik, dan ukuran dari katalog; layanan web dan api dibuat dengan `for_each`.
- Keputusan: preset ukuran, `for_each` alih-alih `count`, `moved` agar server yang sedang melayani tidak diganti (E4 99,9%, E5 300 ms).
- Benang data: inventaris komponen yang menghasilkan data (web, API, database, analytics; E1) dimulai dari label.
- Warisan: repo `koma-infra` bertag `m01`, konvensi label, `log-keputusan.md`.

### Babak 2 — M02: API transaksi tidak lagi dipasang tangan

- Pemicu: tiga usulan anggota tim (VM, Ansible, image siap pakai).
- Tugas tim: mengukur container dan VM, memasang API dengan cloud-init dan Ansible, memanggang image.
- Keputusan: container atau VM per komponen E1; pull atau push untuk 40 server API (C3); bake atau fry.
- Benang data: server API dibuat tanpa data yang harus selamat; data transaksi dipisahkan pada babak 4.
- Warisan: server configuration code dan image API yang dipakai ulang di M06–M10.

### Babak 3 — M03: menutup jalan web ke database

- Pemicu: server web yang disusupi dapat langsung membuka koneksi ke database (A3).
- Tugas tim: VPC dengan tiga tier, ACL per tier, load balancer di depan web; stack jaringan dipisah dari stack aplikasi.
- Keputusan: matriks konektivitas per pasangan tier berdasarkan 78% trafik east-west (E3); egress yang masih terbuka.
- Benang data: database hanya menerima koneksi dari tier API; jalur data menjadi eksplisit.
- Warisan: pola stack jaringan terpisah dan ACL per tier yang dipakai lagi di M06 dan M09.

### Babak 4 — M04: data yang selamat ketika server diganti

- Pemicu: disk database penuh dua kali setahun dan backup malam memperlambat akses dokumen (S5, S6).
- Tugas tim: state remote dengan lock, volume database terpisah, dokumen bersama yang dibaca dua server, bucket unggahan berversi.
- Keputusan: block/file/object untuk S1, S2, S4; batas `size` volume; siapa boleh membaca bucket state.
- Benang data: pemisahan data dari server; object storage untuk unggahan; state sebagai data yang juga harus dilindungi.
- Warisan: bucket state kelompok dipakai semua modul berikutnya.

### Babak 5 — M05: kontraktor pergi, rahasia tertinggal

- Pemicu: laporan pelanggan dapat diunduh siapa saja dan password database ada di repo (A6).
- Tugas tim: mengaudit stack rawan, menulis stack aman dengan password baru dan state terenkripsi, memasang Trivy dan Conftest.
- Keputusan: temuan paling berbahaya; letak rahasia; kebijakan yang menahan bucket publik.
- Benang data: klasifikasi laporan pelanggan sebagai rahasia (A1) menentukan kontrol bucket.
- Warisan: kebijakan Conftest dan enkripsi state dipakai lagi di pipeline M09.

### Babak 6 — M06: API 2.0 tanpa mengganti alamat

- Pemicu: manajemen meminta API 2.0 tanpa mengganti alamat publik dan tanpa jeda yang terasa (L1–L4).
- Tugas tim: mengimpor legacy ke kode, membangun API v2 dengan volume terpisah, memindahkan data, mengalihkan forward, membongkar legacy.
- Keputusan: rehost lalu replatform API, retain database (E8), store and load, kriteria contract.
- Benang data: migrasi data stateful dengan bukti penanda; selisih tulisan selama salin.
- Warisan: API v2 dari kode menjadi target monitoring di M07.

### Babak 7 — M07: tahu lebih dulu daripada pelanggan

- Pemicu: API melambat 40 menit dan diketahui dari keluhan pelanggan; memori dinaikkan manual di konsol (O5).
- Tugas tim: stasiun monitoring sebagai kode, aturan SLO, uji aturan, deteksi drift.
- Keputusan: ambang dan `for:`; anggaran galat 43,2 menit; deteksi lalu rekonsiliasi atau sinkronisasi otomatis.
- Benang data: metrik permintaan, galat, dan latensi sebagai data operasional yang diarsip TSDB.
- Warisan: aturan SLO dipakai untuk menilai canary di M10.

### Babak 8 — M08: setiap rupiah bertuan

- Pemicu: tagihan naik 40% dan server besar di dev menyimpan salinan data pelanggan (G3, A6).
- Tugas tim: modul layanan-web, lingkungan dev/prod dari kode yang sama, label wajib, showback, broker dua penyedia.
- Keputusan: pusat biaya per lingkungan, aturan rahasia hanya di prod, kriteria broker untuk beban analytics (G6).
- Benang data: label `data-class` sebagai metadata tata kelola data; showback biaya per pusat biaya.
- Warisan: modul dan kebijakan tata kelola dipakai di pipeline M09.

### Babak 9 — M09: hanya lewat pipeline

- Pemicu: bucket arsip diganti nama dari konsol dan nama topik salah ketik (H6).
- Tugas tim: memecah stack, menyambungkan lewat state, membuat bucket arsip dan topik di GCP, pipeline dengan uji dan kebijakan, job arsip.
- Keputusan: kontrak output antarstack, perilaku bila GCP putus sehari, kontrol yang mencegah perubahan di luar pipeline.
- Benang data: laporan harian sebagai pipeline data hybrid (H2, H4); topik pesanan sebagai kanal event (H3).
- Warisan: pipeline dan stack GCP dipakai ulang di M10.

### Babak 10 — M10: promo akhir tahun dan rebuild dari nol

- Pemicu: promo akhir tahun melipatgandakan pesanan; direksi bertanya cluster atau serverless (C2, C6).
- Tugas tim: API, Redis, dan worker di cluster sebagai kode; HPA; canary; Cloud Run; rebuild dari namespace kosong lewat pipeline.
- Keputusan: cluster atau serverless, kriteria promosi canary dari metrik M07, apa yang tidak ikut dibangun ulang.
- Benang data: antrean pesanan memisahkan API dari worker; data di Redis tidak ikut dibangun ulang.
- Warisan: ADR akhir dan laporan arsitektur.
