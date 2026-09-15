from django.contrib import admin
from django.contrib.auth.models import Group
from django import forms
from django.db import models
from django.forms import DateInput, TextInput, DateTimeInput, DateTimeField as DateTimeFormField
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import DokumenMasuk, DokumenKeluar, Karyawan, Supplier


class KaryawanDatalistWidget(forms.TextInput):
    def __init__(self, karyawan_list, attrs=None):
        super().__init__(attrs)
        self.karyawan_list = karyawan_list

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        datalist_id = f"{attrs.get('id')}-list"
        options = ''.join(
            f'<option value="{k.nama_lengkap}">{k.kode_karyawan} — {k.jabatan}</option>'
            for k in self.karyawan_list
        )
        datalist = f'<datalist id="{datalist_id}">{options}</datalist>'
        return mark_safe(input_html + datalist)


class TerlambatDiambilFilter(admin.SimpleListFilter):
    title = 'Status Pengambilan'
    parameter_name = 'terlambat'

    def lookups(self, request, model_admin):
        return (
            ('ya', 'Belum diambil > 3 hari'),
            ('tidak', 'Belum melewati 3 hari'),
        )

    def queryset(self, request, queryset):
        batas_pengambilan = timezone.localdate() - timezone.timedelta(days=3)

        if self.value() == 'ya':
            return queryset.filter(
                status='Di Resepsionis',
                tanggal_terima__lt=batas_pengambilan,
            )

        if self.value() == 'tidak':
            return queryset.exclude(
                status='Di Resepsionis',
                tanggal_terima__lt=batas_pengambilan,
            )

        return queryset


@admin.register(DokumenMasuk)
class DokumenMasukAdmin(admin.ModelAdmin):
    list_display = (
        'tanggal_terima',
        'kategori',
        'pengirim',
        'nama_penerima',
        'status',
        'indikator_pengambilan',
        'foto_thumbnail',
    )
    search_fields = ('pengirim', 'nama_penerima')
    autocomplete_fields = ('pt_pengirim',)
    fields = (
        'kategori',
        'jenis_pengirim',
        'pt_pengirim',
        'pengirim',
        'nama_penerima',
        'foto_barang',
        'status',
        'dob_pengambil',
        'tanggal_diambil',
    )
    readonly_fields = ('tanggal_diambil',)
    list_filter = (
        'status',
        'kategori',
        'tanggal_terima',
        TerlambatDiambilFilter,
    )
    ordering = ('-id',)

    @admin.display(description='Indikator')
    def indikator_pengambilan(self, obj):
        if obj.terlambat_diambil:
            return format_html(
                '<strong style="color: #dc2626;">⚠ Terlambat</strong>'
            )
        if obj.status == 'Sudah Diambil':
            return format_html(
                '<span style="color: #16a34a;">✓ Selesai</span>'
            )
        return '-'

    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }

    def foto_thumbnail(self, obj):
        if obj.foto_barang:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_barang.url)
        return "-"
    foto_thumbnail.short_description = "Foto"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
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
                                const selectedOption = ptInput.options && ptInput.selectedIndex >= 0
                                    ? ptInput.options[ptInput.selectedIndex]
                                    : null;
                                pengirimInput.value = selectedOption ? selectedOption.text : '';
                            } else {
                                pengirimInput.value = '';
                            }
                        } else {
                            if (ptWrapper) ptWrapper.style.display = 'none';
                            if (pengirimWrapper) pengirimWrapper.style.display = '';
                            pengirimInput.readOnly = false;
                            pengirimInput.value = '';
                            if (ptInput) {
                                ptInput.value = '';
                                if (window.jQuery) window.jQuery(ptInput).trigger('change');
                            }
                        }
                    }

                    if (jenisInput) jenisInput.addEventListener('change', updatePengirim);
                    if (ptInput) ptInput.addEventListener('change', updatePengirim);
                    updatePengirim();
                });
                </script>
                Pilih <b>PT / Instansi</b> untuk memilih dari Data Supplier dengan pencarian, atau <b>Non-PT / Perseorangan</b> untuk mengetik nama pengirim manual.
            """)
            return formfield

        if db_field.name == 'nama_penerima':
            karyawan_list = list(Karyawan.objects.filter(aktif=True).order_by('nama_lengkap'))
            return forms.CharField(
                label=db_field.verbose_name,
                required=True,
                widget=KaryawanDatalistWidget(
                    karyawan_list,
                    attrs={
                        'style': 'width: 350px;',
                        'list': 'id_nama_penerima-list',
                        'autocomplete': 'off',
                    }
                )
            )

        if db_field.name == 'pengirim':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off', 'id': 'id_pengirim'})

        if isinstance(db_field, models.DateTimeField):
            kwargs['form_class'] = DateTimeFormField
            kwargs['widget'] = DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
            kwargs['input_formats'] = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']
            return db_field.formfield(**kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.jenis_pengirim == 'PT':
            if obj.pt_pengirim:
                obj.pengirim = obj.pt_pengirim.nama_supplier
        else:
            obj.pt_pengirim = None

        super().save_model(request, obj, form, change)


@admin.register(DokumenKeluar)
class DokumenKeluarAdmin(admin.ModelAdmin):
    list_display = ('nomor_resi_internal', 'tanggal_terima', 'nama_pengirim', 'status', 'foto_thumbnail')
    search_fields = ('nomor_resi_internal', 'nama_pengirim')
    list_filter = ('status', 'tanggal_terima')
    ordering = ('-id',)
    readonly_fields = ('nomor_resi_internal',)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'nama_pengirim':
            karyawan_list = list(Karyawan.objects.filter(aktif=True).order_by('nama_lengkap'))
            return forms.CharField(
                label=db_field.verbose_name,
                required=True,
                widget=KaryawanDatalistWidget(
                    karyawan_list,
                    attrs={
                        'style': 'width: 350px;',
                        'list': 'id_nama_pengirim-list',
                        'autocomplete': 'off',
                    }
                )
            )

        if db_field.name == 'resi_jne':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off'})

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def foto_thumbnail(self, obj):
        if obj.foto_dokumen:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_dokumen.url)
        return "-"
    foto_thumbnail.short_description = "Foto"


@admin.register(Karyawan)
class KaryawanAdmin(admin.ModelAdmin):
    list_display = ('kode_karyawan', 'nama_lengkap', 'jabatan', 'tanggal_lahir', 'aktif')
    search_fields = ('kode_karyawan', 'nama_lengkap', 'jabatan')
    list_filter = ('aktif', 'jabatan')
    ordering = ('nama_lengkap',)
    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('kode_supplier', 'nama_supplier')
    search_fields = ('kode_supplier', 'nama_supplier')
    ordering = ('nama_supplier',)


admin.site.site_header = "Dasbor Resepsionis USTP"
admin.site.site_title = "Admin USTP"
admin.site.index_title = "Manajemen Dokumen Internal"

# Semua resepsionis menggunakan hak akses yang sama, jadi Groups tidak perlu ditampilkan.
admin.site.unregister(Group)
