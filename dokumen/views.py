from django.shortcuts import render, redirect
from .models import Karyawan, DokumenMasuk, DokumenKeluar

def lacak_dokumen(request):
    context = {}

    # Setelah verifikasi berhasil, ambil NIK dari session satu kali saja.
    nik_session = request.session.pop('nik_terverifikasi', None)

    if nik_session:
        karyawan = Karyawan.objects.get(nik=nik_session)
        dokumen_keluar = DokumenKeluar.objects.filter(nik_pengirim=nik_session)
        dokumen_masuk = DokumenMasuk.objects.filter(nik_penerima=nik_session)

        context = {
            'karyawan': karyawan,
            'dokumen_masuk': dokumen_masuk,
            'dokumen_keluar': dokumen_keluar,
            'pesan_sukses': 'Verifikasi berhasil. Berikut riwayat dokumen Anda.'
        }
        return render(request, 'lacak_dokumen.html', context)

    # Kalau form dikirim (Karyawan mencet tombol Cari)
    if request.method == 'POST':
        nik_input = request.POST.get('nik')
        dob_input = request.POST.get('tanggal_lahir')

        try:
            # Cek 1: NIK ada di tabel Karyawan nggak?
            karyawan = Karyawan.objects.get(nik=nik_input)

            # Cek 2: Tanggal lahirnya cocok nggak?
            if str(karyawan.tanggal_lahir) == dob_input:
                # Simpan NIK sementara, lalu redirect ke GET.
                # Ini membuat hasil tidak muncul lagi saat halaman di-refresh.
                request.session['nik_terverifikasi'] = nik_input
                return redirect('lacak_dokumen')
            else:
                context['pesan_error'] = "Verifikasi Gagal: Tanggal Lahir tidak cocok!"

        except Karyawan.DoesNotExist:
            context['pesan_error'] = "Verifikasi Gagal: NIK tidak ditemukan dalam sistem!"

    # Kalau cuma buka halaman web biasa (GET request) atau verifikasi gagal
    return render(request, 'lacak_dokumen.html', context)