# PRD: Pengolah Spreadsheet HDUL

Versi: 0.2  
Tanggal: 12 November 2026  
Status: Draf kebutuhan produk berdasarkan diskusi awal

## Klarifikasi terbaru: kolom pembanding dan timestamp

Data awal dan pembanding memiliki `inserted_date`, `updated_date`, `no_surat_kontrol`, dan `respon_bpjs`. Cocokkan dengan left join berdasarkan `id_rencana_kontrol`: data awal berada di kiri, dan nilai dari data pembanding ditambahkan di kanan sebagai kolom baru, termasuk `no_surat_kontrol_baru`, `respon_bpjs_baru`, dan `updated_date_baru`, serta kolom kategori.

Bandingkan `updated_date` awal dan pembanding sekaligus memeriksa isi `no_surat_kontrol` awal dan baru. Perubahan `updated_date` saja belum membuktikan bahwa HDUL menjadi nomor surat. Empat kategori tetap mengacu pada kondisi surat: tidak HDUL, sesuai target, melewati target, dan tidak diubah.

**Menunggu klarifikasi:** apakah durasi dua hari dihitung dari `inserted_date` awal sampai `updated_date_baru`, dan apakah `updated_date` berubah hanya ketika surat kontrol diperbarui atau juga ketika kolom lain berubah? Contoh timestamp dan nilai surat asli yang disamarkan diperlukan untuk menetapkan aturan secara tepat. Jika belum ada pasangan di data pembanding, kolom baru tetap kosong dan baris ditandai belum ada data terbaru.

Klarifikasi ini mengubah usulan tanggal dan bentuk hasil di bagian lain dokumen. Bagian yang menggunakan tanggal pengambilan CSV sebagai dasar durasi merupakan usulan lama dan belum boleh dipakai sebagai aturan final.

## 1. Tujuan produk

Aplikasi Streamlit untuk mengolah spreadsheet pasien ranap yang perlu kontrol ke rajal. Pengguna mengimpor CSV, membersihkan dan menyamakan format data, menambah atau mengedit baris, menggabungkan data berdasarkan `id_rencana_kontrol`, lalu mengunduh hasil olahan.

Tabel di aplikasi menjadi area kerja yang dapat diedit. Hasil left join diberi kategori berdasarkan isi surat pada data awal, isi surat pada data pembanding, dan lama perubahan HDUL menjadi nomor. Hasil utama produk adalah dataset yang telah diperbarui dan bisa digunakan kembali.

## 2. Masalah yang diselesaikan

Pengguna berencana mengambil CSV baru setiap dua hari. Data antarfile perlu dicocokkan agar perubahan nomor surat kontrol dapat diperbarui tanpa menghilangkan kunjungan lama. Pengguna juga memerlukan cara untuk merapikan format dan menambah atau mengoreksi data sebelum mengekspor hasil.

Kolom `no_surat_kontrol` dapat berisi tulisan HDUL, yang berarti harap diisi ulang. Contoh alur: data diambil tanggal 10, kemudian dicocokkan dengan data tanggal 12. Pengguna ingin membedakan surat yang sejak awal tidak HDUL, HDUL yang berubah dalam waktu paling lama dua hari, HDUL yang berubah setelah lebih dari dua hari, dan HDUL yang belum diubah.

Klarifikasi terbaru menggunakan target durasi perubahan paling lama dua hari. Aturan kategori ini menjadi dasar versi 0.2, menggantikan penggunaan H-2 sebelum jadwal kontrol pada draf sebelumnya. Titik awal hitungan dan ketersediaan tanggal perubahan sebenarnya masih perlu dikonfirmasi; struktur CSV belum tersedia untuk diperiksa.

## 3. Dasar keputusan

### Sudah disepakati

| Area | Kebutuhan |
| --- | --- |
| Platform | Streamlit; aplikasi nantinya di-host agar dapat diakses melalui browser. |
| Fungsi utama | Mengedit dan mengolah spreadsheet: tambah data, cleaning, menyamakan data, join, dan ekspor. |
| Input rutin | Satu CSV per pengambilan data; rencana pengambilan setiap dua hari. |
| Pencocokan | Left join data awal dengan data pembanding berdasarkan `id_rencana_kontrol`. |
| HDUL | Isi `no_surat_kontrol` yang mengandung kata HDUL perlu ditindaklanjuti. |
| Tidak HDUL | `no_surat_kontrol` terisi dan tidak mengandung HDUL; penilaian nomor tidak dibatasi ke digit saja. |
| Nilai kosong | Isian kosong atau `-` ditampilkan sebagai `-`. |
| Kategori hasil | Tidak HDUL; sesuai target jika HDUL berubah dalam <= 2 hari; melewati target jika berubah dalam > 2 hari; tidak diubah jika masih HDUL pada data pembanding. |
| Data lama | Kunjungan yang tidak muncul di CSV berikutnya tetap disimpan dengan status terakhir dan keterangan belum ada data terbaru. |
| Cakupan hasil | Data yang masih HDUL dan yang sudah bernomor tetap tersedia. |
| Sistem asal | Penerbitan atau perbaikan surat di sistem asal tetap dilakukan melalui proses yang sudah ada. |

### Usulan perilaku untuk implementasi awal

Bagian berikut merinci perilaku yang diperlukan agar alur dapat diterapkan. Detail ini belum seluruhnya diputuskan dalam diskusi:

- Pengguna memetakan kolom CSV ke kolom kerja karena struktur file belum diketahui.
- Perubahan dipratinjau sebelum diterapkan ke data tersimpan.
- Konflik ID dan nilai yang meragukan ditampilkan untuk diselesaikan pengguna.
- Riwayat dan data kerja disimpan pada penyimpanan persisten yang sesuai dengan hosting.
- Pengguna menentukan tanggal pengambilan data saat impor agar urutan data tidak bergantung pada waktu upload.

## 4. Pengguna dan pekerjaan utama

Pengguna awal adalah petugas yang mengolah data kunjungan dan surat kontrol. Jumlah pengguna, pembagian peran, serta mekanisme akses belum diputuskan.

Pekerjaan utama:

1. Mengimpor CSV hasil ekspor terbaru.
2. Merapikan format kolom agar data dapat dicocokkan.
3. Membandingkan data baru dengan dataset kerja yang sudah tersimpan.
4. Meninjau pembaruan, menambah baris, dan mengedit nilai yang diperlukan.
5. Menerapkan perubahan dan mengunduh CSV hasil olahan.

## 5. Ruang lingkup versi awal

### Termasuk

- Impor CSV dan pratinjau isi file.
- Pemetaan kolom serta validasi data untuk operasi yang dipilih.
- Cleaning dengan aturan yang terlihat dan bisa dipilih pengguna.
- Tabel kerja yang mendukung edit sel dan tambah baris.
- Left join data awal dengan data pembanding melalui `id_rencana_kontrol`.
- Penanganan data baru, pembaruan data lama, serta baris yang tidak mendapat pasangan.
- Empat kategori hasil perbandingan surat kontrol dan perhitungan durasi perubahan jika tanggal acuannya tersedia.
- Penyimpanan data kerja antar-upload.
- Ekspor CSV hasil olahan.

### Di luar versi awal

- Penerbitan nomor surat kontrol secara otomatis.
- Penulisan langsung ke sistem rumah sakit atau sistem penerbit surat.
- Pengiriman pengingat kepada pasien atau petugas.
- Pelacakan kehadiran pasien saat kontrol ke rajal.
- Dashboard analitik sebagai keluaran utama.
- Dukungan XLSX, formula spreadsheet, dan kolaborasi edit serentak, kecuali diputuskan kemudian.

## 6. Alur penggunaan

1. Pengguna menetapkan data awal dari dataset tersimpan atau CSV pertama, misalnya data tanggal 10.
2. Pengguna mengunggah CSV pembanding, misalnya data tanggal 12. Setiap pengambilan data tetap menghasilkan satu CSV.
3. Aplikasi menampilkan pratinjau file dan meminta pemetaan kolom yang belum dikenali.
4. Pengguna memeriksa tanggal pengambilan data dan memilih aturan cleaning.
5. Aplikasi menampilkan hasil cleaning serta masalah yang ditemukan.
6. Aplikasi melakukan left join data awal dengan data pembanding berdasarkan `id_rencana_kontrol`.
7. Pengguna meninjau nilai awal, nilai pembanding, durasi, kategori hasil, baris tanpa pasangan, dan konflik.
8. Pengguna mengedit sel atau menambah baris bila diperlukan.
9. Pengguna menerapkan perubahan ke dataset kerja.
10. Pengguna mengunduh CSV hasil olahan. Dataset tersimpan menjadi dasar pengolahan berikutnya.

Pada impor pertama, baris valid membentuk dataset awal. Impor berikutnya menjadi data pembanding. Nilai dan tanggal awal untuk penilaian tidak boleh hilang ketika nilai kerja diperbarui, agar HDUL tanggal 10 yang baru terlihat berubah tanggal 14 tidak keliru dihitung mulai tanggal 12.

## 7. Kebutuhan fungsional

### FR-01: Impor dan pemetaan kolom

- Aplikasi menerima file CSV dan menampilkan nama kolom serta pratinjau baris sebelum penggabungan.
- Pengguna dapat memilih kolom sumber untuk `id_rencana_kontrol`, `no_surat_kontrol`, serta tanggal acuan yang tersedia. Asal tanggal untuk perhitungan durasi harus ditetapkan setelah contoh data diperiksa.
- Kolom sumber lain dipertahankan untuk pengeditan dan ekspor.
- Jika format pemisah atau encoding tidak dapat dibaca dengan benar, pengguna mendapat penjelasan dan pilihan untuk memperbaiki pembacaan file.
- ID dan nomor surat dibaca sebagai teks agar nol di awal tidak hilang.
- Join hanya dapat diterapkan jika kolom kunci telah dipetakan dan masalah kunci pada baris terkait telah diselesaikan.
- Cleaning dan edit tetap dapat dilakukan saat tanggal acuan belum tersedia; kategori yang memerlukan durasi belum dapat ditentukan.

### FR-02: Cleaning dan penyamaan format

Aturan awal yang diusulkan:

| Operasi | Perilaku |
| --- | --- |
| Spasi | Pangkas spasi di awal dan akhir pada kolom yang dipilih. |
| ID rencana kontrol | Samakan representasi sebagai teks; pertahankan nol di awal dan karakter bermakna. |
| Tanggal | Ubah format sesuai pilihan pengguna; tanggal ambigu atau gagal dibaca ditandai. |
| Pengenalan HDUL | Abaikan perbedaan huruf besar dan kecil saat mendeteksi kata HDUL. |
| Nilai kosong | Tampilkan kosong atau tanda hubung sebagai `-` pada kolom surat kontrol. |
| Duplikat | Tandai ID yang berulang untuk diperiksa sebelum join. |

- Pengguna dapat melihat nilai sebelum dan sesudah cleaning.
- Cleaning tidak mengubah seluruh teks menjadi huruf besar atau menghapus karakter secara menyeluruh tanpa pilihan pengguna.
- Nilai sumber harus tetap dapat ditelusuri selama peninjauan impor.
- Aturan cleaning tambahan menunggu contoh CSV dan kebutuhan nyata pengguna.

### FR-03: Edit dan tambah data

- Pengguna dapat mengedit nilai pada kolom sumber di tabel kerja.
- Pengguna dapat menambahkan baris baru dengan mengisi `id_rencana_kontrol` dan data yang diperlukan.
- Perubahan pada kunci diperiksa kembali terhadap duplikat dan pasangan join.
- Kolom turunan dihitung ulang setelah nilai sumber berubah.
- Pengguna dapat membatalkan perubahan yang belum diterapkan.
- Edit di aplikasi memperbarui dataset kerja dan hasil ekspor. Perubahan tersebut tidak otomatis memperbarui sistem asal.

### FR-04: Join dan pembaruan dataset

Join menggunakan `id_rencana_kontrol` sebagai kunci, data awal sebagai tabel kiri, dan CSV pembanding sebagai tabel kanan. Seluruh penyebutan ID dalam aturan join dan skenario pengujian merujuk pada `id_rencana_kontrol`.

Hasil perbandingan mengikuti left join: semua baris awal dipertahankan; ID yang hanya ada di tabel kanan tidak otomatis masuk hasil perbandingan. Penambahan ID baru ke dataset kerja merupakan operasi terpisah yang dapat dipilih pengguna.

| Kondisi | Hasil yang diusulkan |
| --- | --- |
| ID ada di kedua dataset | Pertahankan nilai awal dan pembanding, hitung kategori, lalu perbarui kolom kerja yang dipilih setelah pengguna menerapkan perubahan. |
| ID hanya ada di dataset tersimpan | Pertahankan baris dan nilai terakhir; tandai belum ada data terbaru. |
| ID hanya ada di CSV baru | Tidak masuk hasil left join. Pengguna dapat menambahkannya ke dataset kerja sebagai rencana kontrol baru melalui operasi terpisah setelah validasi. |
| ID kosong | Tampilkan sebagai masalah; jangan ikutkan baris tersebut dalam join sampai diperbaiki. |
| ID berulang dan pasangan tidak pasti | Tampilkan konflik; jangan memilih salah satu baris secara diam-diam. |

- Jumlah baris sebelum dan sesudah join harus dapat dijelaskan melalui baris yang diperbarui, ditambahkan, dipertahankan, atau tertahan karena konflik.
- Dalam hasil perbandingan dengan kunci unik, jumlah baris sama dengan jumlah baris data awal. Penambahan baris baru ke dataset kerja dilaporkan secara terpisah.
- Simpan `no_surat_kontrol_awal` dan `no_surat_kontrol_pembanding` secara terpisah agar perubahan dapat ditelusuri dan kategori dapat dihitung ulang.
- Nilai kosong dari CSV baru tidak langsung menimpa nilai lama yang sudah terisi. Pengosongan memerlukan pilihan eksplisit pengguna.
- Perubahan dari nomor surat menjadi HDUL tetap ditampilkan sebagai perubahan yang perlu ditinjau.
- Upload ulang file yang sama tidak boleh menambah baris ganda setelah konflik diselesaikan.
- Data yang diambil lebih lama tidak boleh otomatis menimpa data yang lebih baru. Cara menentukan urutan perlu dikonfirmasi bersama mekanisme tanggal pengambilan data.

### FR-05: Pemeriksaan isi surat kontrol

Pemeriksaan dilakukan pada nilai awal dan pembanding, setelah pemangkasan spasi untuk pemeriksaan:

- `mengandung_hdul`: nilai mengandung `hdul`, tanpa membedakan huruf besar dan kecil.
- `terisi_tidak_hdul`: nilai terisi, bukan `-`, dan tidak mengandung `hdul`.
- `kosong`: nilai kosong atau hanya `-`, ditampilkan sebagai `-`.

Aturan pengguna untuk tidak HDUL adalah nilai terisi dan tidak mengandung HDUL. Tidak ditambahkan persyaratan format digit atau pola nomor tertentu. Pemeriksaan ini mengklasifikasikan isi spreadsheet; penerbitan dan pengiriman surat tetap merupakan proses di sistem asal.

### FR-06: Empat kategori hasil perbandingan

Kategori ditentukan berdasarkan kondisi awal, kondisi pembanding, dan durasi perubahan. Setiap baris mendapat paling banyak satu kategori utama.

| Kategori | Kondisi |
| --- | --- |
| 1. Tidak HDUL | Nilai awal sudah terisi dan tidak mengandung HDUL. Tidak perlu menilai durasi perubahan dari HDUL. |
| 2. Sesuai target | Nilai awal mengandung HDUL, nilai pembanding terisi dan tidak mengandung HDUL, dan durasi perubahan <= 2 hari. |
| 3. Melewati target | Nilai awal mengandung HDUL, nilai pembanding terisi dan tidak mengandung HDUL, dan durasi perubahan > 2 hari. |
| 4. Tidak diubah | Nilai awal mengandung HDUL dan pada data pembanding yang cocok masih mengandung HDUL. Lamanya tetap HDUL tidak mengubah kategori ini menjadi melewati target. |

Contoh berikut menggunakan selisih tanggal data awal dan tanggal pertama ditemukan sudah tidak HDUL sebagai usulan dasar hitungan:

| Kondisi awal | Kondisi pembanding | Kategori |
| --- | --- | --- |
| Tanggal 10 sudah ada nomor tanpa HDUL | Tanggal 12 tetap ada nomor | Tidak HDUL |
| Tanggal 10 HDUL | Tanggal 12 terisi tanpa HDUL | Sesuai target, 2 hari |
| Tanggal 10 HDUL | Tanggal 13 terisi tanpa HDUL | Melewati target, 3 hari |
| Tanggal 10 HDUL | Tanggal 14 masih HDUL | Tidak diubah |

#### Dasar waktu yang masih perlu dikonfirmasi

- Usulan awal: `durasi_hari = tanggal_pertama_teramati_tidak_hdul - tanggal_awal_penilaian`, menggunakan selisih tanggal kalender.
- Perlu dikonfirmasi apakah tanggal awal penilaian berasal dari tanggal pengambilan data awal atau kolom tanggal tertentu di CSV.
- Bila sumber menyediakan tanggal perubahan sebenarnya, penggunaan tanggal tersebut perlu diputuskan sebelum implementasi perhitungan.
- CSV berkala hanya membuktikan status saat pengambilan data. Contoh: HDUL tanggal 10 dan sudah terisi tanggal 14 berarti perubahan pertama kali teramati pada tanggal 14; tanggal perubahan sebenarnya bisa lebih awal. Hasil berdasarkan pengamatan tidak boleh diklaim sebagai waktu perubahan yang pasti.
- Tanggal upload tidak otomatis dianggap tanggal pengambilan atau perubahan data.
- Titik awal penilaian dipertahankan pada pembandingan berikutnya; upload baru tidak mengulang hitungan dari nol.

#### Kondisi yang belum dapat dimasukkan ke empat kategori

- ID awal tidak ditemukan di CSV pembanding: pertahankan baris dan status terakhir, tandai belum ada data terbaru. Jangan menyimpulkan tidak diubah dari ketidakhadiran data saja.
- Nilai awal kosong atau `-`: tampilkan `-`; pemetaan ke kategori utama menunggu keputusan pengguna.
- Nilai awal HDUL tetapi nilai pembanding kosong atau `-`: tandai perlu diperiksa; jangan dianggap sudah berubah menjadi nomor.
- HDUL sudah menjadi nilai terisi tanpa HDUL tetapi tanggal durasi belum lengkap: perubahan terlihat, sedangkan kategori sesuai atau melewati target belum dapat ditentukan.
- Nilai awal tidak HDUL tetapi pembanding menjadi HDUL: pertahankan asal kategori awal dan tampilkan perubahan tersebut sebagai masalah untuk diperiksa; aturan penilaian ulang belum diputuskan.

Kolom kategori, durasi, dan ketersediaan data pembanding dipisahkan agar kondisi data tidak tersamarkan oleh satu label. Hasil kategori dapat disertakan dalam ekspor spreadsheet.

### FR-07: Penyimpanan antar-upload

- Dataset kerja yang sudah diterapkan harus dapat dibuka kembali pada sesi berikutnya.
- Restart aplikasi atau berakhirnya sesi browser tidak boleh menghilangkan dataset yang sudah disimpan.
- Simpan asal file dan waktu pemrosesan untuk menelusuri pembaruan.
- Usulan metadata tambahan: tanggal pengambilan data, tanggal pertama suatu ID terlihat, dan tanggal terakhir ID muncul dalam impor.
- Ketidakhadiran baris pada file berikutnya tidak menghapus baris, menyatakan surat selesai, atau memperbarui tanggal terakhir baris tersebut ditemukan.
- Simpan nilai dan tanggal awal penilaian serta tanggal pertama perubahan menjadi tidak HDUL teramati, sehingga pengolahan berikutnya tidak menghilangkan dasar kategori.
- Mekanisme penyimpanan dan lingkup dataset per pengguna atau tim ditetapkan setelah hosting dan akses pengguna diputuskan.

### FR-08: Ekspor

- Pengguna dapat mengunduh dataset hasil olahan sebagai CSV.
- Ekspor mencakup edit yang sudah diterapkan, hasil join, dan kolom sumber yang dipertahankan.
- Kolom turunan atau metadata dapat disertakan melalui pilihan ekspor agar file tetap sesuai kebutuhan pengguna.
- Pengguna dapat membedakan ekspor seluruh dataset dari ekspor baris hasil filter jika fitur filter disediakan.
- Nilai ID dan nomor surat dipertahankan sebagai teks dalam proses pengolahan. Cara membuka file di aplikasi spreadsheet lain perlu diuji karena aplikasi tersebut dapat menafsirkan tipe data sendiri.
- Ekspor tidak menyertakan perubahan yang gagal divalidasi seolah-olah berhasil diterapkan.

## 8. Model data konseptual

Nama berikut adalah nama kerja internal, bukan klaim tentang nama kolom CSV sumber.

| Kelompok | Elemen | Keterangan |
| --- | --- | --- |
| Sumber | `id_rencana_kontrol` | Kunci pencocokan yang disepakati; keunikannya perlu diperiksa pada contoh data. |
| Sumber | `no_surat_kontrol` | Nilai surat yang dapat diedit pada dataset kerja. |
| Perbandingan | `no_surat_kontrol_awal` | Nilai pada data awal penilaian. |
| Perbandingan | `no_surat_kontrol_pembanding` | Nilai pada CSV pembanding, bila pasangan ditemukan. |
| Perbandingan | `tanggal_awal_penilaian` | Asal kolom atau metadata tanggal masih perlu dikonfirmasi. |
| Perbandingan | `tanggal_data_pembanding` | Tanggal keadaan data pembanding, terpisah dari waktu upload. |
| Perbandingan | `tanggal_pertama_teramati_tidak_hdul` | Tanggal pengamatan pertama perubahan HDUL menjadi terisi tanpa HDUL. |
| Sumber | Kolom lainnya | Dipertahankan sesuai file pengguna. |
| Turunan | `kondisi_surat_awal` / `kondisi_surat_pembanding` | Mengandung HDUL, terisi tanpa HDUL, atau kosong. |
| Turunan | `durasi_hari` | Selisih tanggal menurut dasar waktu yang disepakati. |
| Turunan | `kategori_hasil` | Tidak HDUL, sesuai target, melewati target, atau tidak diubah; boleh belum terisi jika bukti tidak lengkap. |
| Metadata | `ketersediaan_data_terbaru` | Muncul atau tidak muncul pada impor terbaru. |
| Metadata | Asal dan tanggal data | Digunakan untuk penelusuran dan urutan pembaruan. |

Jika satu `id_rencana_kontrol` ternyata memiliki beberapa surat atau jadwal kontrol, aturan identitas baris harus ditinjau sebelum join otomatis diterapkan. Baris tersebut tidak boleh digabung menjadi satu tanpa pemeriksaan.

## 9. Kebutuhan operasional

- Aplikasi dijalankan melalui browser menggunakan Streamlit dan disiapkan untuk hosting.
- Penyimpanan harus persisten pada lingkungan hosting yang dipilih.
- Kegagalan impor atau penerapan perubahan tidak boleh meninggalkan dataset tersimpan dalam keadaan setengah diperbarui.
- Pesan masalah menunjukkan baris, kolom, penyebab, dan tindakan perbaikan jika informasi tersedia.
- Target jumlah baris, ukuran file, dan waktu proses ditetapkan setelah contoh CSV tersedia; belum ada target performa yang disepakati.
- Mekanisme login, siapa yang boleh mengakses data, serta penggunaan satu atau beberapa dataset belum diputuskan. Ini perlu ditetapkan sebelum penggunaan dengan data pasien di hosting.

## 10. Kriteria penerimaan versi awal

Contoh berikut adalah data uji buatan.

| ID | Skenario | Hasil yang diharapkan |
| --- | --- | --- |
| AC-01 | CSV berisi `id_rencana_kontrol` bernilai `000123`. | Nol di awal tetap ada selama impor, edit, join, dan ekspor. |
| AC-02 | Nilai surat ` HDuL - harap diisi ulang `. | Diklasifikasikan HDUL. |
| AC-03 | Nilai surat kosong atau `-`. | Ditampilkan sebagai `-` dan belum dianggap bernomor. |
| AC-04 | Data awal tanggal 10 HDUL; pembanding tanggal 12 terisi tanpa HDUL untuk ID yang sama. | Satu baris mendapat kategori sesuai target dengan durasi 2 hari, jika dasar tanggal pengamatan disetujui. |
| AC-05 | ID lama tidak muncul pada CSV berikutnya. | Baris dan nilai terakhir dipertahankan dengan keterangan belum ada data terbaru. |
| AC-06 | CSV baru memuat ID yang tidak ada di data awal. | ID tersebut tidak masuk hasil left join; dapat ditambahkan terpisah ke dataset kerja setelah validasi. |
| AC-07 | Satu ID muncul berulang sehingga pasangan join tidak pasti. | Konflik ditampilkan dan baris tidak digabung secara diam-diam. |
| AC-08 | Baris tidak memiliki ID. | Pengguna dapat memperbaikinya; baris tidak ikut join sebelum valid. |
| AC-09 | Pengguna mengedit nilai atau menambah baris, lalu menerapkan dan mengekspor. | Hasil ekspor memuat perubahan tersebut dan kolom turunan dihitung ulang. |
| AC-10 | Pengguna membatalkan edit yang belum diterapkan. | Dataset tersimpan tetap seperti sebelumnya. |
| AC-11 | File yang sama diimpor ulang. | Tidak terbentuk baris ganda. |
| AC-12 | Data awal tanggal 10 HDUL; tanggal 14 masih HDUL pada ID yang cocok. | Kategori tidak diubah, bukan melewati target. |
| AC-13 | HDUL sudah berubah menjadi terisi tanpa HDUL, tetapi tanggal acuan belum tersedia. | Cleaning, edit, dan join tetap bisa dilakukan; kategori sesuai atau melewati target belum dapat ditentukan. |
| AC-14 | Aplikasi dimulai ulang setelah data diterapkan. | Dataset tersimpan dapat dibuka kembali. |
| AC-15 | CSV baru berisi surat kosong untuk baris lama yang sudah bernomor. | Nomor lama tidak otomatis terhapus; pengguna mendapat pilihan penanganan. |
| AC-16 | Nilai surat awal terisi, bukan `-`, dan tidak mengandung HDUL. | Kategori tidak HDUL sesuai aturan isi yang ditetapkan pengguna, tanpa menambah aturan pola nomor. |
| AC-17 | Impor gagal sebelum perubahan diterapkan. | Dataset tersimpan tidak berubah. |
| AC-18 | Data awal tanggal 10 HDUL; pembanding tanggal 13 pertama kali terisi tanpa HDUL. | Kategori melewati target dengan durasi 3 hari, jika dasar tanggal pengamatan disetujui. |
| AC-19 | ID awal HDUL tidak ditemukan di CSV pembanding. | Baris dipertahankan dengan keterangan belum ada data terbaru; tidak otomatis diberi kategori tidak diubah. |
| AC-20 | Awal tanggal 10 HDUL, tanggal 12 masih HDUL, tanggal 14 pertama kali terisi tanpa HDUL. | Tanggal awal tetap 10; durasi teramati 4 hari, bukan 2 hari akibat hitungan diulang pada tanggal 12. |
| AC-21 | Kedua tabel memiliki kunci unik dan CSV pembanding memiliki ID tambahan. | Jumlah baris hasil left join sama dengan jumlah baris awal; ID tambahan tidak masuk otomatis. |
| AC-22 | Nilai awal HDUL dan pasangan pembanding berisi `-`. | Ditandai perlu diperiksa; tidak dianggap berhasil berubah menjadi nomor. |

## 11. Hal yang perlu divalidasi

| Hal terbuka | Dampak pada implementasi |
| --- | --- |
| Contoh CSV dan nama kolom sebenarnya | Menetapkan pemetaan, tipe data, dan aturan cleaning. |
| Tanggal awal penilaian berasal dari metadata pengambilan atau kolom CSV | Menetapkan titik awal target durasi dua hari. |
| Cakupan ekspor tiap dua hari | Menentukan pembacaan kelengkapan pembaruan; data lama tetap dipertahankan. |
| Keunikan `id_rencana_kontrol` | Menentukan apakah diperlukan kunci tambahan untuk satu baris. |
| Contoh isi surat selain HDUL, kosong, dan `-` | Menguji aturan terisi tanpa HDUL yang telah ditetapkan pengguna. |
| Hari kalender atau hari kerja untuk target dua hari | Menetapkan cara menghitung durasi; contoh sementara memakai selisih tanggal kalender. |
| Ketersediaan tanggal perubahan sebenarnya | Membedakan durasi perubahan sebenarnya dari durasi saat perubahan pertama teramati. |
| Kategori untuk nilai awal kosong, hasil pembanding kosong, dan perubahan kembali menjadi HDUL | Melengkapi penanganan kasus di luar empat kondisi utama. |
| Tanggal pengambilan data dan identitas data awal | Menetapkan urutan pembaruan dan mempertahankan dasar penilaian antar-impor. |
| Kolom yang diperbarui dan prioritas edit manual terhadap impor berikutnya | Menentukan aturan saat nilai lama, edit, dan data baru berbeda. |
| Hosting, pengguna, dan akses | Menentukan penyimpanan persisten dan pembatasan akses. |
| Kolom ekspor yang dibutuhkan | Menentukan apakah metadata dan kolom turunan disertakan. |
| Ukuran CSV yang nyata | Menetapkan uji kapasitas dan target waktu proses. |

## 12. Urutan implementasi yang diusulkan

1. Periksa contoh CSV dan tetapkan kontrak kolom, identitas baris, serta aturan cleaning.
2. Bangun impor, pemetaan kolom, tabel edit, tambah baris, dan ekspor.
3. Tambahkan join, pratinjau perubahan, penanganan konflik, dan penyimpanan antar-upload.
4. Tambahkan empat kategori perbandingan serta perhitungan durasi perubahan setelah tanggal acuan dan aturannya tervalidasi.
5. Uji kriteria penerimaan menggunakan data samaran, lalu siapkan hosting sesuai keputusan akses dan penyimpanan.
