# Pengolah data kontrol

Aplikasi Streamlit untuk membersihkan CSV atau XLSX, membandingkan data awal dan pembanding berdasarkan `id_rencana_kontrol`, serta mengekspor hasil CSV. Untuk XLSX, aplikasi membaca sheet pertama.

## Menjalankan

Pasang Python 3.10 atau lebih baru, lalu jalankan:

```bash
python -m venv .venv
```

Di Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Unggah CSV atau Excel awal; kolom wajib dan pemisah CSV dikenali otomatis. Tinjau dan simpan hasil, lalu unggah file pembanding. Baris dengan ID baru pada file pembanding otomatis ditambahkan di bagian bawah hasil dengan seluruh kolomnya. Kolom hasil pembanding yang nilainya sama dengan data awal ditampilkan kosong dan diekspor kosong; nilai sebenarnya tetap tersimpan untuk perhitungan. Kategori awal menandai HDUL atau Tidak HDUL, termasuk isian kosong sebagai Tidak HDUL.

Jika HDUL sudah menjadi nomor surat, target dihitung berdasarkan selisih tanggal `inserted_date` awal dan `updated_date` baru: 0 sampai 2 hari termasuk sesuai target, lebih dari 2 hari melewati target. Nilai `updated_date` tidak harus berbeda dari data awal. Jam tetap ditampilkan pada `durasi_jam` tetapi tidak menentukan batas target. Timestamp harus berformat ISO, misalnya `2026-01-10 14:30:00`. Kolom kosong atau `-` tidak dianggap nomor. ID kosong dan duplikat harus diperbaiki sebelum impor.

Untuk HDUL yang masih belum berubah, aplikasi memakai tanggal pengambilan file sebagai batas hitung: sampai 2 hari adalah `Belum diubah, masih dalam target`, lebih dari itu `Belum diubah, melewati target`. Tanggal otomatis diisi hari ini sesuai waktu Jakarta dan bisa diubah saat impor. Jika ID tidak ditemukan dalam impor terbaru, hanya `ketersediaan_data` yang ditandai `Belum ada data terbaru`. Kategori, nilai pembanding, durasi, dan tanggal pengambilan data terakhir tetap disimpan sampai ID tersebut ditemukan lagi; ketidakhadiran ID tidak menjadi bukti perubahan status.

Dataset dibaca dan disimpan hanya pada tab `Data` di Google Sheets. Tab ini menyimpan nilai pembanding secara lengkap; nilai yang sama tetap disembunyikan pada tampilan aplikasi dan ekspor CSV. Jika tab `Data` berasal dari versi sebelumnya, impor kembali data terbaru untuk melengkapi nilai pembanding yang sebelumnya disembunyikan. Edit langsung di tab tersebut dapat tertimpa saat aplikasi menyimpan. Letakkan tepat satu file JSON service account di folder `data`, aktifkan Google Sheets API, dan bagikan spreadsheet ke email service account sebagai Editor.

Di Streamlit Community Cloud, masukkan kredensial service account dalam format TOML di Secrets dengan bagian `[gcp_service_account]`. Aplikasi tidak meminta kata sandi; siapa pun yang bisa mengakses aplikasi dapat melihat dataset.

Kolom pembanding diperbarui dengan mengimpor CSV terbaru. Data dari versi aplikasi lama tidak dihapus; gunakan `HDUL_DB_PATH` untuk memilih database baru, lalu impor ulang data awal.
