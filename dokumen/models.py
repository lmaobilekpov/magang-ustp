from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Karyawan(models.Model):
    kode_karyawan = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Kode Karyawan"
    )
    nama_lengkap = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    jabatan = models.CharField(
        max_length=255,
        verbose_name="Jabatan"
    )
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = 'Karyawan'
        verbose_name_plural = 'Data Karyawan'
        ordering = ['nama_lengkap']

    def __str__(self):
        return f"{self.nama_lengkap} ({self.kode_karyawan})"


class Supplier(models.Model):
    kode_supplier = models.CharField(max_length=100, unique=True, verbose_name="Kode Supplier")
    nama_supplier = models.CharField(max_length=255, verbose_name="Nama Supplier")

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Data Supplier'
        ordering = ['nama_supplier']

    def __str__(self):
        return f"{self.nama_supplier} ({self.kode_supplier})"


class DokumenMasuk(models.Model):
    KATEGORI_CHOICES = [
        ('Surat Resmi', 'Surat Resmi'),
        ('Paket Pribadi', 'Paket Pribadi'),
    ]

    STATUS_CHOICES = [
        ('Di Resepsionis', 'Di Resepsionis'),
        ('Sudah Diambil', 'Sudah Diambil'),
    ]

    JENIS_PENGIRIM_CHOICES = [
        ('PT', 'PT / Instansi'),
        ('Non-PT', 'Non-PT / Perseorangan'),
    ]

    tanggal_terima = models.DateField(auto_now_add=True)
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES)
    jenis_pengirim = models.CharField(
        max_length=20,
        choices=JENIS_PENGIRIM_CHOICES,
        default='PT',
        verbose_name="Jenis Pengirim"
    )
    pt_pengirim = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="PT / Instansi Pengirim"
    )
    pengirim = models.CharField(max_length=255, verbose_name="Nama Pengirim")
    nama_penerima = models.CharField(max_length=255, verbose_name="Nama Penerima")
    foto_barang = models.ImageField(upload_to='foto_barang/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Di Resepsionis')
    dob_pengambil = models.DateField(
        blank=True,
        null=True,
        verbose_name="Tanggal Lahir Pengambil (Verifikasi)",
        help_text="Sebutkan tanggal lahir saat pengambilan barang untuk verifikasi identitas."
    )
    tanggal_diambil = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Waktu Pengambilan Barang"
    )

    class Meta:
        verbose_name_plural = 'Dokumen Masuk'

    @property
    def terlambat_diambil(self):
        if self.status != 'Di Resepsionis' or not self.tanggal_terima:
            return False

        batas_pengambilan = timezone.localdate() - timezone.timedelta(days=3)
        return self.tanggal_terima < batas_pengambilan

    def clean(self):
        super().clean()

        if not self.nama_penerima or not self.nama_penerima.strip():
            raise ValidationError({
                'nama_penerima': 'Nama penerima wajib diisi.'
            })

        nama_penerima = self.nama_penerima.strip()
        karyawan_cocok = Karyawan.objects.filter(
            nama_lengkap__iexact=nama_penerima
        ).first()

        if self.pk:
            data_lama = DokumenMasuk.objects.get(pk=self.pk)
            nama_lama = (data_lama.nama_penerima or '').strip()
            nama_tidak_diubah = nama_lama.casefold() == nama_penerima.casefold()
        else:
            nama_tidak_diubah = False

        if not karyawan_cocok or (not karyawan_cocok.aktif and not nama_tidak_diubah):
            raise ValidationError({
                'nama_penerima': 'Nama penerima harus sesuai dengan data karyawan yang masih aktif.'
            })

        if self.status == 'Sudah Diambil':
            if not self.dob_pengambil:
                raise ValidationError({
                    'dob_pengambil': 'Tanggal Lahir Pengambil wajib diisi jika status dokumen Sudah Diambil.'
                })

            if karyawan_cocok.tanggal_lahir != self.dob_pengambil:
                raise ValidationError({
                    'dob_pengambil': 'Tanggal lahir tidak sesuai dengan data karyawan penerima.'
                })

    def save(self, *args, **kwargs):
        if self.pk:
            data_lama = DokumenMasuk.objects.get(pk=self.pk)

            if data_lama.status == 'Sudah Diambil' and self.status == 'Sudah Diambil':
                self.tanggal_diambil = data_lama.tanggal_diambil
            elif self.status == 'Sudah Diambil':
                self.tanggal_diambil = timezone.now()
            else:
                self.tanggal_diambil = None
        else:
            if self.status == 'Sudah Diambil':
                self.tanggal_diambil = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.kategori} - {self.nama_penerima}"


class DokumenKeluar(models.Model):
    STATUS_CHOICES = [
        ('Menunggu Kurir', 'Menunggu Kurir'),
        ('Sudah Diserahkan ke JNE', 'Sudah Diserahkan ke JNE'),
        ('Paket Kembali', 'Paket Kembali'),
    ]

    nomor_resi_internal = models.CharField(max_length=20, unique=True, blank=True)
    tanggal_terima = models.DateField(auto_now_add=True)
    nama_pengirim = models.CharField(max_length=255)
    deskripsi = models.TextField()
    foto_dokumen = models.ImageField(upload_to='foto_dokumen/', blank=True, null=True)
    resi_jne = models.URLField(blank=True, null=True, verbose_name="URL Resi JNE")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Menunggu Kurir')

    def clean(self):
        super().clean()

        if not self.nama_pengirim or not self.nama_pengirim.strip():
            raise ValidationError({
                'nama_pengirim': 'Nama pengirim wajib diisi.'
            })

        nama_pengirim = self.nama_pengirim.strip()
        karyawan_cocok = Karyawan.objects.filter(
            nama_lengkap__iexact=nama_pengirim
        ).first()

        if self.pk:
            data_lama = DokumenKeluar.objects.get(pk=self.pk)
            nama_lama = (data_lama.nama_pengirim or '').strip()
            nama_tidak_diubah = nama_lama.casefold() == nama_pengirim.casefold()
        else:
            nama_tidak_diubah = False

        if not karyawan_cocok or (not karyawan_cocok.aktif and not nama_tidak_diubah):
            raise ValidationError({
                'nama_pengirim': 'Nama pengirim harus sesuai dengan data karyawan yang masih aktif.'
            })

        if self.status == 'Sudah Diserahkan ke JNE' and not self.resi_jne:
            raise ValidationError({
                'resi_jne': 'URL Resi JNE wajib diisi jika status sudah diserahkan ke JNE.'
            })

        if self.status == 'Paket Kembali':
            if not self.pk:
                raise ValidationError({
                    'status': 'Paket Kembali hanya dapat digunakan untuk transaksi yang sudah diserahkan ke JNE.'
                })

            data_lama = DokumenKeluar.objects.get(pk=self.pk)
            if data_lama.status not in ('Sudah Diserahkan ke JNE', 'Paket Kembali'):
                raise ValidationError({
                    'status': 'Dokumen harus berstatus Sudah Diserahkan ke JNE sebelum ditandai Paket Kembali.'
                })

            if not self.resi_jne:
                raise ValidationError({
                    'resi_jne': 'URL Resi JNE wajib diisi untuk menandai paket sebagai Paket Kembali.'
                })

    class Meta:
        verbose_name_plural = 'Dokumen Keluar'

    def save(self, *args, **kwargs):
        if self.nomor_resi_internal:
            super().save(*args, **kwargs)
            return

        from django.db import IntegrityError, transaction

        today = timezone.now().date()
        date_str = today.strftime("%Y%m%d")

        for _ in range(5):
            try:
                with transaction.atomic():
                    nomor_terakhir = DokumenKeluar.objects.filter(
                        tanggal_terima=today,
                        nomor_resi_internal__startswith=f"OUT-{date_str}-"
                    ).order_by('-nomor_resi_internal').first()

                    if nomor_terakhir:
                        nomor_terakhir = int(
                            nomor_terakhir.nomor_resi_internal.split('-')[-1]
                        )
                        new_number = nomor_terakhir + 1
                    else:
                        new_number = 1

                    self.nomor_resi_internal = f"OUT-{date_str}-{new_number:03d}"
                    super().save(*args, **kwargs)

                return

            except IntegrityError:
                self.nomor_resi_internal = ""

        raise IntegrityError("Gagal membuat nomor resi internal yang unik.")

    def __str__(self):
        return f"{self.nomor_resi_internal} - {self.nama_pengirim}"


class RiwayatStatusDokumenMasuk(models.Model):
    dokumen = models.ForeignKey(
        DokumenMasuk,
        on_delete=models.CASCADE,
        related_name='riwayat_status',
    )
    status_sebelumnya = models.CharField(max_length=50, blank=True, null=True, verbose_name='Status Sebelumnya')
    status = models.CharField(max_length=50, choices=DokumenMasuk.STATUS_CHOICES)
    diubah_pada = models.DateTimeField(auto_now_add=True)
    diubah_oleh = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='riwayat_dokumen_masuk',
    )

    class Meta:
        verbose_name = 'Riwayat Status Dokumen Masuk'
        verbose_name_plural = 'Riwayat Status Dokumen Masuk'
        ordering = ['-diubah_pada']


class RiwayatStatusDokumenKeluar(models.Model):
    dokumen = models.ForeignKey(
        DokumenKeluar,
        on_delete=models.CASCADE,
        related_name='riwayat_status',
    )
    status_sebelumnya = models.CharField(max_length=50, blank=True, null=True, verbose_name='Status Sebelumnya')
    status = models.CharField(max_length=50, choices=DokumenKeluar.STATUS_CHOICES)
    diubah_pada = models.DateTimeField(auto_now_add=True)
    diubah_oleh = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='riwayat_dokumen_keluar',
    )

    class Meta:
        verbose_name = 'Riwayat Status Dokumen Keluar'
        verbose_name_plural = 'Riwayat Status Dokumen Keluar'
        ordering = ['-diubah_pada']
