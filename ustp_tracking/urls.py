from django.contrib import admin
from django.urls import path
from dokumen import views  # Import file views yang baru aja lu bikin

urlpatterns = [
    # Ini pintu belakang buat lu dan resepsionis
    path('admin/', admin.site.urls),
    
    # Ini pintu depan (Portal Karyawan), roket Django resmi digusur!
    path('', views.lacak_dokumen, name='lacak_dokumen'), 
]