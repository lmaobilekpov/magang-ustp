from django.db.models import Count, Q
from django.utils import timezone

from .models import DokumenMasuk, DokumenKeluar


def dashboard_stats(request):
    if not request.path.startswith('/admin/') or not request.user.is_authenticated or not request.user.is_staff:
        return {}

    batas_pengambilan = timezone.localdate() - timezone.timedelta(days=3)
    return {
        'dashboard_stats': {
            'masuk_resepsionis': DokumenMasuk.objects.filter(status='Di Resepsionis').count(),
            'masuk_terlambat': DokumenMasuk.objects.filter(
                status='Di Resepsionis', tanggal_terima__lt=batas_pengambilan
            ).count(),
            'masuk_diambil': DokumenMasuk.objects.filter(status='Sudah Diambil').count(),
            'keluar_menunggu': DokumenKeluar.objects.filter(status='Menunggu Kurir').count(),
            'keluar_jne': DokumenKeluar.objects.filter(status='Sudah Diserahkan ke JNE').count(),
            'keluar_kembali': DokumenKeluar.objects.filter(status='Paket Kembali').count(),
        }
    }
