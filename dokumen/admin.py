from django.contrib import admin
from django.db import models
from django.forms import DateInput, TextInput, DateTimeInput, DateTimeField as DateTimeFormField
from django.utils.html import format_html
from django.utils.safestring import mark_safe 
from .models import DokumenMasuk, DokumenKeluar, Karyawan, DataPT

@admin.register(DokumenMasuk)
class DokumenMasukAdmin(admin.ModelAdmin):
    list_display = ('tanggal_terima', 'kategori', 'pengirim', 'nama_penerima', 'status', 'foto_thumbnail')
    search_fields = ('pengirim', 'nama_penerima', 'nik_penerima')
    fields = (
        'kategori',
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
        # 1. Combobox Nama Penerima + NIK otomatis
        if db_field.name == 'nama_penerima':
            karyawan_list = Karyawan.objects.all()
            options = "".join([
                f'<option value="{k.nama_lengkap}" data-nik="{k.nik}">' 
                for k in karyawan_list
            ])
            datalist = f'<datalist id="list_nama_penerima">{options}</datalist>'

            kwargs['widget'] = TextInput(
                attrs={
                    'autocomplete': 'off',
                    'list': 'list_nama_penerima',
                    'id': 'id_nama_penerima'
                }
            )

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe(
                datalist + """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_penerima');
                    const nikInput = document.getElementById('id_nik_penerima');
                    const datalist = document.getElementById('list_nama_penerima');

                    function updateNIK() {
                        const pilihan = Array.from(datalist.options).find(
                            option => option.value === namaInput.value
                        );

                        if (pilihan) {
                            nikInput.value = pilihan.dataset.nik;
                        }
                    }

                    namaInput.addEventListener('input', updateNIK);
                    namaInput.addEventListener('change', updateNIK);
                });
                </script>
                """
            )
            return formfield

        # 2. NIK Penerima tetap bisa diketik manual untuk edge case
        elif db_field.name == 'nik_penerima':
            karyawan_list = Karyawan.objects.all()
            options = "".join([
                f'<option value="{k.nik}">' 
                for k in karyawan_list
            ])
            datalist = f'<datalist id="list_nik_penerima">{options}</datalist>'

            kwargs['widget'] = TextInput(
                attrs={
                    'autocomplete': 'off',
                    'list': 'list_nik_penerima',
                    'id': 'id_nik_penerima'
                }
            )

            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe(
                datalist + "Pilih dari daftar atau ketik manual."
            )
            return formfield

        # 3. Tetap matikan autocomplete untuk pengirim biasa
        elif db_field.name == 'pengirim':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off'})

        # 4. Override DateTimeField agar bisa parsing format ISO
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
        if db_field.name == 'nama_pengirim':
            karyawan_list = Karyawan.objects.all()

            options = "".join([
                f'<option value="{k.nama_lengkap}" data-nik="{k.nik}">'
                for k in karyawan_list
            ])

            datalist = f'<datalist id="list_nama_pengirim">{options}</datalist>'

            kwargs['widget'] = TextInput(
                attrs={
                    'autocomplete': 'off',
                    'list': 'list_nama_pengirim',
                    'id': 'id_nama_pengirim'
                }
            )

            formfield = super().formfield_for_dbfield(
                db_field, request, **kwargs
            )

            formfield.help_text = mark_safe(
                datalist + """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_pengirim');
                    const nikInput = document.getElementById('id_nik_pengirim');
                    const datalist = document.getElementById('list_nama_pengirim');

                    function updateNIK() {
                        const pilihan = Array.from(datalist.options).find(
                            option => option.value === namaInput.value
                        );

                        if (pilihan) {
                            nikInput.value = pilihan.dataset.nik;
                        } else {
                            nikInput.value = '';
                        }
                    }

                    namaInput.addEventListener('input', updateNIK);
                    namaInput.addEventListener('change', updateNIK);
                });
                </script>
                """
            )

            return formfield

        elif db_field.name == 'nik_pengirim':
            kwargs['widget'] = TextInput(
                attrs={
                    'readonly': 'readonly',
                    'id': 'id_nik_pengirim'
                }
            )

            return super().formfield_for_dbfield(
                db_field, request, **kwargs
            )

        return super().formfield_for_dbfield(
            db_field, request, **kwargs
        )

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

# Kustomisasi Teks Django Admin
admin.site.site_header = "Dasbor Resepsionis USTP"
admin.site.site_title = "Admin USTP"
admin.site.index_title = "Manajemen Dokumen Internal"
