from datetime import timedelta

from django.shortcuts import render, redirect
from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    Karyawan,
    DokumenMasuk,
    DokumenKeluar,
    RiwayatStatusDokumenMasuk,
    RiwayatStatusDokumenKeluar,
)

RIWAYAT_PORTAL_HARI = 365


def render_portal(request, template_name, context=None):
    response = render(request, template_name, context or {})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def lacak_dokumen(request):
    """Halaman verifikasi identitas karyawan."""
    context = {}

    if request.method == 'POST':
        dob_input = request.POST.get('tanggal_lahir')

        if not dob_input:
            context['pesan_error'] = 'Silakan masukkan tanggal lahir.'
            return render_portal(request, 'lacak_dokumen.html', context)

        karyawan_list = list(Karyawan.objects.filter(tanggal_lahir=dob_input))

        if not karyawan_list:
            context['pesan_error'] = 'Verifikasi gagal: tanggal lahir tidak ditemukan dalam sistem.'
        elif len(karyawan_list) > 1:
            context['pesan_error'] = 'Verifikasi gagal: tanggal lahir cocok dengan lebih dari satu karyawan. Silakan hubungi resepsionis.'
        else:
            request.session['karyawan_terverifikasi'] = karyawan_list[0].pk
            return redirect('riwayat_dokumen')

    return render_portal(request, 'lacak_dokumen.html', context)


def riwayat_dokumen(request):
    """Halaman riwayat dokumen karyawan setelah verifikasi."""
    karyawan_id = request.session.get('karyawan_terverifikasi')

    if not karyawan_id:
        return redirect('lacak_dokumen')

    try:
        karyawan = Karyawan.objects.get(pk=karyawan_id)
    except Karyawan.DoesNotExist:
        request.session.pop('karyawan_terverifikasi', None)
        return redirect('lacak_dokumen')

    batas_riwayat = timezone.localdate() - timedelta(days=RIWAYAT_PORTAL_HARI)
    riwayat_masuk = RiwayatStatusDokumenMasuk.objects.order_by('diubah_pada')
    riwayat_keluar = RiwayatStatusDokumenKeluar.objects.order_by('diubah_pada')

    dokumen_masuk = DokumenMasuk.objects.filter(
        nama_penerima=karyawan.nama_lengkap,
        tanggal_terima__gte=batas_riwayat,
    ).prefetch_related(
        Prefetch(
            'riwayat_status',
            queryset=riwayat_masuk,
            to_attr='riwayat_status_timeline',
        )
    )
    dokumen_keluar = DokumenKeluar.objects.filter(
        nama_pengirim=karyawan.nama_lengkap,
        tanggal_terima__gte=batas_riwayat,
    ).prefetch_related(
        Prefetch(
            'riwayat_status',
            queryset=riwayat_keluar,
            to_attr='riwayat_status_timeline',
        )
    )

    context = {
        'karyawan': karyawan,
        'dokumen_masuk': dokumen_masuk,
        'dokumen_keluar': dokumen_keluar,
        'batas_riwayat': batas_riwayat,
        'retensi_hari': RIWAYAT_PORTAL_HARI,
    }
    return render_portal(request, 'riwayat_dokumen.html', context)


def keluar_portal(request):
    request.session.pop('karyawan_terverifikasi', None)
    return redirect('lacak_dokumen')
