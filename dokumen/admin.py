from django.contrib import admin
from django.contrib.auth.models import Group
from django import forms
from django.db import models
from django.forms import DateInput, TextInput, DateTimeInput, DateTimeField as DateTimeFormField
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    DokumenMasuk,
    DokumenKeluar,
    Karyawan,
    Supplier,
    RiwayatStatusDokumenMasuk,
    RiwayatStatusDokumenKeluar,
)


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
        return mark_safe(input_html + f'<datalist id="{datalist_id}">{options}</datalist>')


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
            return queryset.filter(status='Di Resepsionis', tanggal_terima__lt=batas_pengambilan)
        if self.value() == 'tidak':
            return queryset.exclude(status='Di Resepsionis', tanggal_terima__lt=batas_pengambilan)
        return queryset


class DokumenMasukForm(forms.ModelForm):
    class Meta:
        model = DokumenMasuk
        fields = '__all__'

    def clean_pengirim(self):
        pengirim = (self.cleaned_data.get('pengirim') or '').strip()
        jenis_pengirim = self.cleaned_data.get('jenis_pengirim')
        pt_pengirim = self.cleaned_data.get('pt_pengirim')

        if jenis_pengirim == 'PT' and pt_pengirim:
            return pt_pengirim.nama_supplier

        return pengirim


class RiwayatMasukInline(admin.TabularInline):
    model = RiwayatStatusDokumenMasuk
    extra = 0
    can_delete = False
    readonly_fields = ('perubahan_status', 'diubah_pada', 'diubah_oleh')
    fields = ('perubahan_status', 'diubah_pada', 'diubah_oleh')
    verbose_name = 'Perubahan Status'
    verbose_name_plural = 'Riwayat Perubahan Status'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    @admin.display(description='Perubahan Status')
    def perubahan_status(self, obj):
        if not obj.status_sebelumnya:
            return format_html('<strong>Status awal:</strong> {}', obj.status)
        return format_html('<strong>{}</strong> &nbsp;→&nbsp; <strong>{}</strong>', obj.status_sebelumnya, obj.status)


class RiwayatKeluarInline(admin.TabularInline):
    model = RiwayatStatusDokumenKeluar
    extra = 0
    can_delete = False
    readonly_fields = ('perubahan_status', 'diubah_pada', 'diubah_oleh')
    fields = ('perubahan_status', 'diubah_pada', 'diubah_oleh')
    verbose_name = 'Perubahan Status'
    verbose_name_plural = 'Riwayat Perubahan Status'
    classes = ('status-history-inline',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    @admin.display(description='Perubahan Status')
    def perubahan_status(self, obj):
        if not obj.status_sebelumnya:
            return format_html('<strong>Status awal:</strong> {}', obj.status)
        return format_html('<strong>{}</strong> &nbsp;→&nbsp; <strong>{}</strong>', obj.status_sebelumnya, obj.status)


@admin.register(DokumenMasuk)
class DokumenMasukAdmin(admin.ModelAdmin):
    form = DokumenMasukForm
    list_display = ('tanggal_terima', 'kategori', 'pengirim', 'nama_penerima', 'status', 'indikator_pengambilan', 'foto_thumbnail')
    search_fields = ('pengirim', 'nama_penerima')
    autocomplete_fields = ('pt_pengirim', 'karyawan_penerima')
    fields = ('kategori', 'jenis_pengirim', 'pt_pengirim', 'pengirim', 'karyawan_penerima', 'nama_penerima', 'foto_barang', 'status', 'dob_pengambil', 'tanggal_diambil')
    readonly_fields = ('tanggal_diambil', 'nama_penerima')
    list_filter = ('status', 'kategori', 'tanggal_terima', TerlambatDiambilFilter)
    ordering = ('-id',)
    inlines = (RiwayatMasukInline,)

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }
        js = ('js/dokumen_masuk_form.js',)

    @admin.display(description='Indikator')
    def indikator_pengambilan(self, obj):
        if obj.terlambat_diambil:
            return format_html('<strong style="color: #dc2626;">{}</strong>', '⚠ Terlambat')
        if obj.status == 'Sudah Diambil':
            return mark_safe('<span style="color: #16a34a;">✓ Selesai</span>')
        return '-'

    formfield_overrides = {models.DateField: {'widget': DateInput(attrs={'type': 'date'})}}

    def foto_thumbnail(self, obj):
        if obj.foto_barang:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_barang.url)
        return '-'
    foto_thumbnail.short_description = 'Foto'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'jenis_pengirim':
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.help_text = mark_safe('Pilih <b>PT / Instansi</b> untuk memilih dari Data Supplier dengan pencarian, atau <b>Non-PT / Perseorangan</b> untuk mengetik nama pengirim manual.')
            return formfield
        if db_field.name == 'pengirim':
            kwargs['required'] = False
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off', 'id': 'id_pengirim'})
        if isinstance(db_field, models.DateTimeField):
            kwargs['form_class'] = DateTimeFormField
            kwargs['widget'] = DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
            kwargs['input_formats'] = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = DokumenMasuk.objects.get(pk=obj.pk).status
        if obj.jenis_pengirim == 'PT' and obj.pt_pengirim:
            obj.pengirim = obj.pt_pengirim.nama_supplier
        elif obj.jenis_pengirim != 'PT':
            obj.pt_pengirim = None
        super().save_model(request, obj, form, change)
        if not change or old_status != obj.status:
            RiwayatStatusDokumenMasuk.objects.create(
                dokumen=obj,
                status_sebelumnya=old_status,
                status=obj.status,
                diubah_oleh=request.user,
            )


@admin.register(DokumenKeluar)
class DokumenKeluarAdmin(admin.ModelAdmin):
    list_display = ('nomor_resi_internal', 'tanggal_terima', 'nama_pengirim', 'status', 'foto_thumbnail')
    search_fields = ('nomor_resi_internal', 'nama_pengirim')
    list_filter = ('status', 'tanggal_terima')
    ordering = ('-id',)
    readonly_fields = ('nomor_resi_internal',)
    inlines = (RiwayatKeluarInline,)

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'nama_pengirim':
            karyawan_list = list(Karyawan.objects.filter(aktif=True).order_by('nama_lengkap'))
            return forms.CharField(label=db_field.verbose_name, required=True, widget=KaryawanDatalistWidget(karyawan_list, attrs={'style': 'width: 350px;', 'list': 'id_nama_pengirim-list', 'autocomplete': 'off'}))
        if db_field.name == 'resi_jne':
            kwargs['widget'] = TextInput(attrs={'autocomplete': 'off'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def foto_thumbnail(self, obj):
        if obj.foto_dokumen:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', obj.foto_dokumen.url)
        return '-'
    foto_thumbnail.short_description = 'Foto'

    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            old_status = DokumenKeluar.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)
        if not change or old_status != obj.status:
            RiwayatStatusDokumenKeluar.objects.create(
                dokumen=obj,
                status_sebelumnya=old_status,
                status=obj.status,
                diubah_oleh=request.user,
            )


@admin.register(Karyawan)
class KaryawanAdmin(admin.ModelAdmin):
    list_display = ('kode_karyawan', 'nama_lengkap', 'jabatan', 'tanggal_lahir', 'aktif')
    search_fields = ('kode_karyawan', 'nama_lengkap', 'jabatan')
    list_filter = ('aktif', 'jabatan')
    ordering = ('nama_lengkap',)
    formfield_overrides = {models.DateField: {'widget': DateInput(attrs={'type': 'date'})}}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('kode_supplier', 'nama_supplier')
    search_fields = ('kode_supplier', 'nama_supplier')
    ordering = ('nama_supplier',)


admin.site.site_header = 'Dasbor Resepsionis USTP'
admin.site.site_title = 'Admin USTP'
admin.site.index_title = 'Manajemen Dokumen Internal'
admin.site.unregister(Group)
