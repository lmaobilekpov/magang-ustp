from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Karyawan(models.Model):
    nik = models.CharField(max_length=50, unique=True, verbose_name="NIK")
    nama_lengkap = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")

    class Meta:
        verbose_name = 'Karyawan'
        verbose_name_plural = 'Data Karyawan'
        ordering = ['nama_lengkap']

    def __str__(self):
        return f"{self.nama_lengkap} ({self.nik})"

class DokumenMasuk(models.Model):
    KATEGORI_CHOICES = [
        ('Surat Resmi', 'Surat Resmi'),
        ('Paket Pribadi', 'Paket Pribadi'),
        ('Inventaris IT', 'Inventaris IT'),
    ]

    STATUS_CHOICES = [
        ('Di Resepsionis', 'Di Resepsionis'),
        ('Sudah Diambil', 'Sudah Diambil'),
    ]

    tanggal_terima = models.DateField(auto_now_add=True)
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES)
    pengirim = models.CharField(max_length=255)
    nama_penerima = models.CharField(max_length=255)
    nik_penerima = models.CharField(max_length=50, verbose_name="NIK penerima")
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

            
            # Cari data karyawan berdasarkan NIK
                        # Cari data karyawan berdasarkan NIK
            karyawan_asli = Karyawan.objects.filter(
                nik=self.nik_penerima
            ).first()

            # NIK wajib terdaftar di data HRD
            if not karyawan_asli:
                raise ValidationError({
                    'nik_penerima': 'NIK tidak terdaftar di data HRD!'
                })

            # Cek apakah nama penerima cocok dengan data HRD
            if self.nama_penerima.strip().casefold() != karyawan_asli.nama_lengkap.strip().casefold():
                raise ValidationError({
                    'nama_penerima': 'Nama tidak sesuai dengan NIK!'                
                    })

            # Cek apakah tanggal lahir cocok dengan data HRD
            if self.dob_pengambil != karyawan_asli.tanggal_lahir:
                raise ValidationError({
                    'dob_pengambil': 'Tanggal lahir salah!'
                })
                # Cek apakah nama penerima cocok dengan data HRD
                if self.nama_penerima.strip().casefold() != karyawan_asli.nama_lengkap.strip().casefold():
                    raise ValidationError({
                        'nama_penerima': 'Verifikasi Gagal: Nama penerima tidak cocok dengan data HRD!'
                    })

                # Cek apakah tanggal lahir cocok dengan data HRD
                if self.dob_pengambil != karyawan_asli.tanggal_lahir:
                    raise ValidationError({
                        'dob_pengambil': 'Verifikasi Gagal: Tanggal lahir tidak cocok dengan data HRD!'
                    })
    def save(self, *args, **kwargs):
        from django.utils import timezone

        if self.pk:
            data_lama = DokumenMasuk.objects.get(pk=self.pk)

            if data_lama.status == 'Sudah Diambil':
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
        ('Sedang Dikirim JNE', 'Sedang Dikirim JNE'),
        ('Selesai', 'Selesai'),
    ]

    nomor_resi_internal = models.CharField(max_length=20, unique=True, blank=True)
    tanggal_terima = models.DateField(auto_now_add=True)
    nama_pengirim = models.CharField(max_length=255)
    nik_pengirim = models.CharField(max_length=50, verbose_name="NIK pengirim")
    deskripsi = models.TextField()
    foto_dokumen = models.ImageField(upload_to='foto_dokumen/', blank=True, null=True)
    resi_jne = models.URLField(blank=True, null=True, verbose_name="URL Resi JNE")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Menunggu Kurir')

    class Meta:
        verbose_name_plural = 'Dokumen Keluar'

    def save(self, *args, **kwargs):
        if not self.nomor_resi_internal:
            today = timezone.now().date()
            # Mencari dokumen yang dibuat hari ini
            count = DokumenKeluar.objects.filter(tanggal_terima=today).count()
            new_number = count + 1
            date_str = today.strftime("%Y%m%d")
            self.nomor_resi_internal = f"OUT-{date_str}-{new_number:03d}"

        super().save(*args, **kwargs)

    
    def __str__(self):
        return f"{self.nomor_resi_internal} - {self.nama_pengirim}"
