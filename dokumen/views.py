from django.shortcuts import render, redirect
from .models import Karyawan, DokumenMasuk, DokumenKeluar


def render_portal(request, context=None):
    response = render(request, 'lacak_dokumen.html', context or {})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def lacak_dokumen(request):
    context = {}
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
        return render_portal(request, context)

    if request.method == 'POST':
        nik_input = request.POST.get('nik')
        dob_input = request.POST.get('tanggal_lahir')

        try:
            karyawan = Karyawan.objects.get(nik=nik_input)

            if str(karyawan.tanggal_lahir) == dob_input:
                request.session['nik_terverifikasi'] = nik_input
                return redirect('lacak_dokumen')
            else:
                context['pesan_error'] = "Verifikasi Gagal: Tanggal Lahir tidak cocok!"

        except Karyawan.DoesNotExist:
            context['pesan_error'] = "Verifikasi Gagal: NIK tidak ditemukan dalam sistem!"

    return render_portal(request, context)
