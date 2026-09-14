from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Karyawan(models.Model):
    kode_karyawan = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Kode Karyawan"
    )
    nama_lengkap = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    jabatan = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Jabatan"
    )
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")

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

    def clean(self):
        super().clean()

        if self.status == 'Sudah Diambil':
            if not self.dob_pengambil:
                raise ValidationError({
                    'dob_pengambil': 'Tanggal Lahir Pengambil wajib diisi jika status dokumen Sudah Diambil.'
                })

            karyawan_cocok = Karyawan.objects.filter(
                nama_lengkap__iexact=self.nama_penerima.strip(),
                tanggal_lahir=self.dob_pengambil,
            ).first()

            if not karyawan_cocok:
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

        if self.status == 'Sudah Diserahkan ke JNE' and not self.resi_jne:
            raise ValidationError({
                'resi_jne': 'URL Resi JNE wajib diisi jika status sudah diserahkan ke JNE.'
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
