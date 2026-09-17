from django.contrib import admin
from django.urls import path
from dokumen import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.lacak_dokumen, name='lacak_dokumen'),
    path('dokumen-aktif/', views.dokumen_aktif, name='dokumen_aktif'),
    path('riwayat/', views.riwayat_dokumen, name='riwayat_dokumen'),
    path('keluar/', views.keluar_portal, name='keluar_portal'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
