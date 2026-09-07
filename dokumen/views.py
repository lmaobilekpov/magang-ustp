from django.shortcuts import render
from .models import Karyawan, DokumenMasuk, DokumenKeluar

def lacak_dokumen(request):
    context = {}
    
    # Kalau form dikirim (Karyawan mencet tombol Cari)
    if request.method == 'POST':
        nik_input = request.POST.get('nik')
        dob_input = request.POST.get('tanggal_lahir') # Format dari HTML biasanya YYYY-MM-DD

        try:
            # Cek 1: NIK ada di tabel Karyawan nggak?
            karyawan = Karyawan.objects.get(nik=nik_input)
            
            # Cek 2: Tanggal lahirnya cocok nggak?
            if str(karyawan.tanggal_lahir) == dob_input:
                
                # Verifikasi sukses! Tarik semua dokumen milik NIK ini
                # (Pastikan nama field 'nik_pengirim' dsb sesuai dengan yang ada di models.py lu)
                dokumen_keluar = DokumenKeluar.objects.filter(nik_pengirim=nik_input)
                dokumen_masuk = DokumenMasuk.objects.filter(nik_penerima=nik_input) 
                
                context = {
                    'karyawan': karyawan,
                    'dokumen_masuk': dokumen_masuk,
                    'dokumen_keluar': dokumen_keluar,
                    'pesan_sukses': 'Verifikasi berhasil. Berikut riwayat dokumen Anda.'
                }
                return render(request, 'lacak_dokumen.html', context)
            else:
                context['pesan_error'] = "Verifikasi Gagal: Tanggal Lahir tidak cocok!"
                
        except Karyawan.DoesNotExist:
            context['pesan_error'] = "Verifikasi Gagal: NIK tidak ditemukan dalam sistem!"

    # Kalau cuma buka halaman web biasa (GET request) atau verifikasi gagal
    return render(request, 'lacak_dokumen.html', context)