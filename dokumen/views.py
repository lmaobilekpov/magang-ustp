from django.shortcuts import render, redirect
from django.db.models import Prefetch
from .models import (
    Karyawan,
    DokumenMasuk,
    DokumenKeluar,
    RiwayatStatusDokumenKeluar,
)


def render_portal(request, context=None):
    response = render(request, 'lacak_dokumen.html', context or {})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def lacak_dokumen(request):
    context = {}
    karyawan_id = request.session.pop('karyawan_terverifikasi', None)

    if karyawan_id:
        try:
            karyawan = Karyawan.objects.get(pk=karyawan_id)
        except Karyawan.DoesNotExist:
            context['pesan_error'] = 'Data karyawan tidak ditemukan dalam sistem.'
            return render_portal(request, context)

        riwayat_keluar = RiwayatStatusDokumenKeluar.objects.order_by('diubah_pada')
        dokumen_keluar = DokumenKeluar.objects.filter(
            nama_pengirim=karyawan.nama_lengkap
        ).prefetch_related(
            Prefetch(
                'riwayat_status',
                queryset=riwayat_keluar,
                to_attr='riwayat_status_timeline',
            )
        )
        dokumen_masuk = DokumenMasuk.objects.filter(nama_penerima=karyawan.nama_lengkap)

        context = {
            'karyawan': karyawan,
            'dokumen_masuk': dokumen_masuk,
            'dokumen_keluar': dokumen_keluar,
            'pesan_sukses': 'Verifikasi berhasil. Berikut riwayat dokumen Anda.'
        }
        return render_portal(request, context)

    if request.method == 'POST':
        dob_input = request.POST.get('tanggal_lahir')

        if not dob_input:
            context['pesan_error'] = 'Silakan masukkan tanggal lahir.'
            return render_portal(request, context)

        karyawan_list = list(Karyawan.objects.filter(tanggal_lahir=dob_input))

        if not karyawan_list:
            context['pesan_error'] = 'Verifikasi Gagal: Tanggal Lahir tidak ditemukan dalam sistem!'
        elif len(karyawan_list) > 1:
            context['pesan_error'] = 'Verifikasi Gagal: Tanggal Lahir cocok dengan lebih dari satu karyawan. Silakan hubungi resepsionis.'
        else:
            request.session['karyawan_terverifikasi'] = karyawan_list[0].pk
            return redirect('lacak_dokumen')

    return render_portal(request, context)
