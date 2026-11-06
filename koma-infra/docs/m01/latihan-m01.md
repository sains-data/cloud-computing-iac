# Latihan 1.1 — Memilih dari katalog, bukan mengetik angka

| Hal | Isi |
|---|---|
| Nama | |
| NIM | |
| Kelompok | `k0_` |
| Kasus | |

Berkas ini ditulis sendiri. Keluaran plan berasal dari akun AWS Anda; penjelasannya dengan kata-kata Anda
sendiri. Simpan di folder mata kuliah, di luar repo `koma-infra`, lalu unggah bersama
`bukti/bukti-m01.json` (setelah E.1, potret terakhir kosong) ke tugas **Latihan Mandiri di Lab — Modul 01**.

## L.1 — `api` naik ke ukuran `sedang`

Blok plan yang memuat baris berubah:

```text

```

Simbol (`~` atau `-/+`) dan alasannya. Apa yang dilakukan provider terhadap instance saat
`instance_type` berubah, dan apa artinya bagi server yang sedang melayani pengguna?

## L.2 — `web` pindah ke Debian 12 (tidak di-apply)

Blok plan dengan `must be replaced` dan `# forces replacement`, beserta baris ringkasannya:

```text

```

Simbol, atribut pemicunya, apa yang hilang bersama instance lama, dan konsekuensinya bagi pengguna.
Mengapa ringkasannya memuat `1 to change` dan `1 to destroy` sekaligus?

## L.3 — Ukuran di luar katalog

Pesan galat `tofu plan` dengan ukuran `raksasa`:

```text

```

Kapan galat ini muncul (sebelum atau sesudah menghubungi AWS) dan mengapa itu penting:

## L.4 — Bukti

- Waktu `koma cek m01` (WIB):
- Nomor potret:
- `Latihan lulus` di keluaran `koma cek`:
- Tipe instance `api` setelah apply (dari `tofu output instance`):
- Plan sesudah apply berakhir `exit code = …`:
