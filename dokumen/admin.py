from django.contrib import admin
from django.db import models
from django.forms import DateInput, TextInput, DateTimeInput, DateTimeField as DateTimeFormField, Select
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import DokumenMasuk, DokumenKeluar, Karyawan, DataPT

@admin.register(DokumenMasuk)
class DokumenMasukAdmin(admin.ModelAdmin):
    list_display = ('tanggal_terima', 'kategori', 'pengirim', 'nama_penerima', 'status', 'foto_thumbnail')
    search_fields = ('pengirim', 'nama_penerima', 'nik_penerima')
    fields = (
        'kategori',
        'jenis_pengirim',
        'pt_pengirim',
        'pengirim',
        'nama_penerima',
        'nik_penerima',
        'foto_barang',
        'status',
        'dob_pengambil',
        'tanggal_diambil',
    )
    readonly_fields = ('tanggal_diambil',)
    list_filter = ('status', 'kategori', 'tanggal_terima')
    ordering = ('-id',)
    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }

    def foto_thumbnail(self, obj):
        if obj.foto_barang:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_barang.url)
        return "-"
    foto_thumbnail.short_description = "Foto"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Jenis pengirim: PT / Instansi atau Non-PT / Perseorangan
        if db_field.name == 'jenis_pengirim':
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe("""
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const jenisInput = document.getElementById('id_jenis_pengirim');
                    const ptInput = document.getElementById('id_pt_pengirim');
                    const pengirimInput = document.getElementById('id_pengirim');
                    const ptWrapper = ptInput ? ptInput.closest('.form-row') : null;
                    const pengirimWrapper = pengirimInput ? pengirimInput.closest('.form-row') : null;

                    function updatePengirim() {
                        if (!jenisInput || !pengirimInput) return;

                        if (jenisInput.value === 'PT') {
                            if (ptWrapper) ptWrapper.style.display = '';
                            if (pengirimWrapper) pengirimWrapper.style.display = 'none';
                            pengirimInput.readOnly = true;

                            if (ptInput && ptInput.value) {
                                pengirimInput.value = ptInput.options[ptInput.selectedIndex].text;
                            } else {
                                pengirimInput.value = '';
                            }
                        } else {
                            if (ptWrapper) ptWrapper.style.display = 'none';
                            if (pengirimWrapper) pengirimWrapper.style.display = '';
                            pengirimInput.readOnly = false;
                        }
                    }

                    if (jenisInput) jenisInput.addEventListener('change', updatePengirim);
                    if (ptInput) ptInput.addEventListener('change', updatePengirim);
                    updatePengirim();
                });
                </script>
                Pilih <b>PT / Instansi</b> untuk memilih dari Data PT, atau <b>Non-PT / Perseorangan</b> untuk mengetik nama pengirim manual.
            """)
            return formfield

        # Nama penerima: dropdown dari Data Karyawan
        if db_field.name == 'nama_penerima':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nama_lengkap, f'{k.nama_lengkap} ({k.nik})') for k in karyawan_list
            ]

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.widget = Select(attrs={'style': 'width: 300px;'})
            formfield.choices = choices
            return formfield

        # NIK penerima: dropdown dari Data Karyawan
        if db_field.name == 'nik_penerima':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nik, k.nik) for k in karyawan_list
            ]

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.widget = Select(attrs={'style': 'width: 300px;'})
            formfield.choices = choices
            return formfield

        # Pengirim tetap menjadi input manual untuk Non-PT dan disembunyikan lewat JS saat PT
        if db_field.name == 'pengirim':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off', 'id': 'id_pengirim'})

        # Override DateTimeField agar bisa parsing format datetime-local
        if isinstance(db_field, models.DateTimeField):
            kwargs['form_class'] = DateTimeFormField
            kwargs['widget'] = DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
            kwargs['input_formats'] = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']
            return db_field.formfield(**kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(DokumenKeluar)
class DokumenKeluarAdmin(admin.ModelAdmin):
    list_display = ('nomor_resi_internal', 'tanggal_terima', 'nama_pengirim', 'status', 'foto_thumbnail')
    search_fields = ('nomor_resi_internal', 'nama_pengirim', 'nik_pengirim')
    list_filter = ('status', 'tanggal_terima')
    ordering = ('-id',)
    readonly_fields = ('nomor_resi_internal',)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Nama pengirim: dropdown dari Data Karyawan
        if db_field.name == 'nama_pengirim':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nama_lengkap, f'{k.nama_lengkap} ({k.nik})') for k in karyawan_list
            ]

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.widget = Select(attrs={'style': 'width: 300px;'})
            formfield.choices = choices
            return formfield

        # NIK pengirim: dropdown dari Data Karyawan
        if db_field.name == 'nik_pengirim':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nik, k.nik) for k in karyawan_list
            ]

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.widget = Select(attrs={'style': 'width: 300px;'})
            formfield.choices = choices
            return formfield

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def foto_thumbnail(self, obj):
        if obj.foto_dokumen:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_dokumen.url)
        return "-"
    foto_thumbnail.short_description = "Foto"

@admin.register(Karyawan)
class KaryawanAdmin(admin.ModelAdmin):
    list_display = ('nik', 'nama_lengkap', 'tanggal_lahir')
    search_fields = ('nik', 'nama_lengkap')
    ordering = ('nama_lengkap',)
    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }

@admin.register(DataPT)
class DataPTAdmin(admin.ModelAdmin):
    list_display = ('nama_pt',)
    search_fields = ('nama_pt',)
    ordering = ('nama_pt',)

admin.site.site_header = "Dasbor Resepsionis USTP"
admin.site.site_title = "Admin USTP"
admin.site.index_title = "Manajemen Dokumen Internal"
