from django.contrib import admin
from django.urls import path
from dokumen import views  # Import file views yang baru aja lu bikin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.lacak_dokumen, name='lacak_dokumen'),
]

urlpatterns = [
    # Ini pintu belakang buat lu dan resepsionis
    path('admin/', admin.site.urls),
    
    # Ini pintu depan (Portal Karyawan), roket Django resmi digusur!
    path('', views.lacak_dokumen, name='lacak_dokumen'), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)