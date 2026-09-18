import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ustp_tracking.settings')
django.setup()

from dokumen.models import Karyawan, DokumenMasuk, DokumenKeluar
from django.core.exceptions import ValidationError
from django.utils import timezone

print("--- Memulai Simulasi Skenario Negatif ---")

# 1. Karyawan dengan Nama Lengkap Kembar (Duplikat)
print("\n[1] Menguji Karyawan dengan Nama Lengkap Kembar")
Karyawan.objects.filter(nama_lengkap='Kembar Identik').delete()
k1 = Karyawan.objects.create(kode_karyawan='KEMB01', nama_lengkap='Kembar Identik', jabatan='Staff', tanggal_lahir=date(1990, 1, 1))
k2 = Karyawan.objects.create(kode_karyawan='KEMB02', nama_lengkap='Kembar Identik', jabatan='Manager', tanggal_lahir=date(1995, 5, 5))

# Coba ambil barang dengan nama 'Kembar Identik' tapi dengan DOB Karyawan 2 (1995)
doc = DokumenMasuk(kategori='Paket Pribadi', pengirim='Pengirim', nama_penerima='Kembar Identik', status='Sudah Diambil', dob_pengambil=date(1995, 5, 5))
try:
    doc.clean()
    print("SUCCESS: Bisa memverifikasi Karyawan 2 (DOB 1995)")
except ValidationError as e:
    print("FAILED (Bug!): Gagal memverifikasi Karyawan 2, sistem membaca Karyawan 1 saja ->", e)

# Coba ambil dengan DOB Karyawan 1 (1990)
doc.dob_pengambil = date(1990, 1, 1)
try:
    doc.clean()
    print("SUCCESS: Bisa memverifikasi Karyawan 1 (DOB 1990)")
except ValidationError as e:
    print("FAILED: ->", e)


# 2. Race Condition / Transaksi Dokumen Keluar jika IntegrityError gagal ditangani dengan retry
print("\n[2] Menguji Limit Retry Nomor Resi Internal (Dokumen Keluar)")
# Kita tidak bisa dengan mudah mensimulasikan concurrent save() yang race dari script sinkron tanpa threading,
# Tapi kita tahu bahwa loop akan gagal setelah 5 kali if IntegrityError terus-menerus.
print("INFO: Retry mechanism sudah memiliki limit 5. Jika terjadi race condition masif >5 concurrent req, sistem akan raise IntegrityError (500 Error di client) daripada silent fail.")

# 3. Validasi Dokumen Masuk dengan Karyawan Nonaktif vs Karyawan Aktif dengan Nama Sama
print("\n[3] Menguji Karyawan Non-aktif dengan Nama Sama dengan Karyawan Aktif")
Karyawan.objects.filter(nama_lengkap='Budi AktifNonaktif').delete()
k3_nonaktif = Karyawan.objects.create(kode_karyawan='BUD01', nama_lengkap='Budi AktifNonaktif', jabatan='Staff', tanggal_lahir=date(1980, 1, 1), aktif=False)
k4_aktif = Karyawan.objects.create(kode_karyawan='BUD02', nama_lengkap='Budi AktifNonaktif', jabatan='SPV', tanggal_lahir=date(1985, 2, 2), aktif=True)

doc2 = DokumenMasuk(kategori='Paket Pribadi', pengirim='Pengirim', nama_penerima='Budi AktifNonaktif', status='Di Resepsionis')
try:
    doc2.clean()
    print("SUCCESS: Berhasil memvalidasi nama 'Budi AktifNonaktif' karena ada yang masih aktif.")
except ValidationError as e:
    print("FAILED (Bug!): Sistem membaca data yang Non-aktif karena `first()` mengambil data pertama tanpa peduli aktif/tidak ->", e)

# 4. Potensi Bypass URL Resi JNE dengan Whitespace
print("\n[4] Menguji Input Resi JNE hanya berisi spasi kosong (Whitespace Bypass)")
Karyawan.objects.filter(nama_lengkap='Test Pengirim').delete()
k5 = Karyawan.objects.create(kode_karyawan='PENG01', nama_lengkap='Test Pengirim', jabatan='Staff', tanggal_lahir=date(1992, 1, 1), aktif=True)

doc_keluar = DokumenKeluar(nama_pengirim='Test Pengirim', deskripsi='Paket penting', status='Sudah Diserahkan ke JNE', resi_jne='   ')
try:
    doc_keluar.clean()
    print("FAILED (Bug!): Sistem menerima URL resi yang hanya berisi spasi (whitespace).")
except ValidationError as e:
    print("SUCCESS: Sistem menolak URL resi whitespace ->", e)

# Bersihkan Data
k1.delete()
k2.delete()
k3_nonaktif.delete()
k4_aktif.delete()
k5.delete()
print("\n--- Simulasi Selesai ---")
