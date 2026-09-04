from django.contrib import admin
from django.db import models
from django.forms import DateInput, TextInput
from .models import DokumenMasuk, DokumenKeluar

@admin.register(DokumenMasuk)
class DokumenMasukAdmin(admin.ModelAdmin):
    list_display = ('tanggal_terima', 'kategori', 'pengirim', 'nama_penerima', 'status')
    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ['pengirim', 'nama_penerima', 'nik_penerima']:
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(DokumenKeluar)
class DokumenKeluarAdmin(admin.ModelAdmin):
    list_display = ('nomor_resi_internal', 'tanggal_terima', 'nama_pengirim', 'status')
    readonly_fields = ('nomor_resi_internal',)

# Kustomisasi Teks Django Admin
admin.site.site_header = "Dasbor Resepsionis USTP"
admin.site.site_title = "Admin USTP"
admin.site.index_title = "Manajemen Dokumen Internal"
