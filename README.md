# Manajemen Dokumen Internal - PT USTP

Proyek ini adalah sistem *tracking* dokumen internal berbasis **Django** yang dirancang khusus untuk divisi resepsionis/administrasi PT USTP. Proyek ini saat ini berada pada tahap **Minimum Viable Product (MVP)** yang memanfaatkan kapabilitas penuh dari Django Admin yang telah dikustomisasi.

## ✨ Fitur Saat Ini (MVP)

### 1. Manajemen Dokumen Masuk
- Pencatatan paket/surat yang masuk (pengirim, penerima, kategori surat/paket).
- Upload bukti foto barang/dokumen (dengan fitur pratinjau *thumbnail* langsung di tabel).
- Status *tracking*: "Di Resepsionis" dan "Sudah Diambil".
- **Verifikasi Keamanan:** Mensyaratkan input Tanggal Lahir (`dob_pengambil`) sebagai *2-Factor Authentication* manual saat ada yang mengambil barang.
- Pencatatan waktu pengambilan yang presisi dengan antarmuka kalender *native*.

### 2. Manajemen Dokumen Keluar
- Fitur auto-generate "Nomor Resi Internal" secara cerdas berdasarkan tanggal (Contoh: `OUT-20260904-001`).
- Status pengiriman: "Menunggu Kurir", "Sedang Dikirim JNE", dan "Selesai".
- Validasi wajib input untuk nomor resi eksternal (JNE) jika dokumen diproses.

### 3. Dasbor Resepsionis (Custom Django Admin)
- Kustomisasi Logo dan Judul Dasbor (*Header* & *Site Title*).
- **Filter Pintar:** Menyediakan panel filter sidebar (berdasarkan Status, Kategori, dan Tanggal).
- **Pencarian:** Kolom pencarian otomatis untuk mencari berdasarkan Nama, NIK, atau Nomor Resi.
- *Collapsible Recent Actions* pada halaman utama untuk tampilan yang lebih lega.
- Semua tabel otomatis diurutkan dari data yang paling baru diinput.
- Seluruh antarmuka telah disesuaikan dengan zona waktu **WIB (Asia/Jakarta)** dan menggunakan Bahasa Indonesia.

## 🚀 Cara Menjalankan (Development)
1. Aktifkan *virtual environment*: `.\env\Scripts\activate`
2. Jalankan server lokal: `python manage.py runserver`
3. Buka browser pada alamat: `http://127.0.0.1:8000/admin`
