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
        # 1. Pilih jenis pengirim + tampilkan field sesuai pilihan
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

                    if (jenisInput) {
                        jenisInput.addEventListener('change', updatePengirim);
                    }
                    if (ptInput) {
                        ptInput.addEventListener('change', updatePengirim);
                    }

                    updatePengirim();
                });
                </script>
                Pilih <b>PT / Instansi</b> untuk memilih dari Data PT, atau <b>Non-PT / Perseorangan</b> untuk mengetik nama pengirim manual.
            """)
            return formfield

        # 2. Nama Penerima dibuat dropdown biasa
        if db_field.name == 'nama_penerima':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nama_lengkap, k.nama_lengkap) for k in karyawan_list
            ]

            current_value = request.POST.get('nama_penerima') if request.method == 'POST' else request.GET.get('nama_penerima')
            if current_value and current_value not in [value for value, label in choices]:
                choices.append((current_value, current_value))

            kwargs['widget'] = Select(attrs={'id': 'id_nama_penerima'})
            kwargs['choices'] = choices
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe("""
                Pilih nama karyawan dari daftar.
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_penerima');
                    const nikInput = document.getElementById('id_nik_penerima');

                    const dataKaryawan = {
                        %s
                    };

                    function updateNIK() {
                        if (namaInput && nikInput) {
                            nikInput.value = dataKaryawan[namaInput.value] || '';
                        }
                    }

                    if (namaInput) namaInput.addEventListener('change', updateNIK);
                    updateNIK();
                });
                </script>
            """ % ','.join([
                f'{k.nama_lengkap!r}: {k.nik!r}' for k in karyawan_list
            ]))
            return formfield

        # 3. NIK Penerima juga dibuat dropdown dan tetap sinkron dengan Nama
        elif db_field.name == 'nik_penerima':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nik, k.nik) for k in karyawan_list
            ]

            kwargs['widget'] = Select(attrs={'id': 'id_nik_penerima'})
            kwargs['choices'] = choices
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe("""
                Pilih NIK dari daftar.
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_penerima');
                    const nikInput = document.getElementById('id_nik_penerima');
                    const dataKaryawan = {
                        %s
                    };

                    const dataNik = {};
                    Object.keys(dataKaryawan).forEach(function(nama) {
                        dataNik[dataKaryawan[nama]] = nama;
                    });

                    if (nikInput) {
                        nikInput.addEventListener('change', function() {
                            if (namaInput) namaInput.value = dataNik[nikInput.value] || '';
                        });
                    }
                });
                </script>
            """ % ','.join([
                f'{k.nama_lengkap!r}: {k.nik!r}' for k in karyawan_list
            ]))
            return formfield

        # 4. Pengirim tetap berupa input tersembunyi saat PT, manual saat Non-PT
        elif db_field.name == 'pengirim':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off', 'id': 'id_pengirim'})

        # 5. Override DateTimeField agar bisa parsing format ISO
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
        # 1. Nama Pengirim dibuat dropdown karyawan
        if db_field.name == 'nama_pengirim':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nama_lengkap, k.nama_lengkap) for k in karyawan_list
            ]

            kwargs['widget'] = Select(attrs={'id': 'id_nama_pengirim'})
            kwargs['choices'] = choices
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe("""
                Pilih nama karyawan dari daftar.
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_pengirim');
                    const nikInput = document.getElementById('id_nik_pengirim');
                    const dataKaryawan = {
                        %s
                    };

                    function updateNIK() {
                        if (namaInput && nikInput) {
                            nikInput.value = dataKaryawan[namaInput.value] || '';
                        }
                    }

                    if (namaInput) namaInput.addEventListener('change', updateNIK);
                    updateNIK();
                });
                </script>
            """ % ','.join([
                f'{k.nama_lengkap!r}: {k.nik!r}' for k in karyawan_list
            ]))
            return formfield

        # 2. NIK Pengirim juga dibuat dropdown
        elif db_field.name == 'nik_pengirim':
            karyawan_list = Karyawan.objects.all()
            choices = [('', '---------')] + [
                (k.nik, k.nik) for k in karyawan_list
            ]

            kwargs['widget'] = Select(attrs={'id': 'id_nik_pengirim'})
            kwargs['choices'] = choices
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe("""
                Pilih NIK dari daftar.
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const namaInput = document.getElementById('id_nama_pengirim');
                    const nikInput = document.getElementById('id_nik_pengirim');
                    const dataKaryawan = {
                        %s
                    };

                    const dataNik = {};
                    Object.keys(dataKaryawan).forEach(function(nama) {
                        dataNik[dataKaryawan[nama]] = nama;
                    });

                    if (nikInput) {
                        nikInput.addEventListener('change', function() {
                            if (namaInput) namaInput.value = dataNik[nikInput.value] || '';
                        });
                    }
                });
                </script>
            """ % ','.join([
                f'{k.nama_lengkap!r}: {k.nik!r}' for k in karyawan_list
            ]))
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

# Kustomisasi Teks Django Admin
admin.site.site_header = "Dasbor Resepsionis USTP"
admin.site.site_title = "Admin USTP"
admin.site.index_title = "Manajemen Dokumen Internal"
