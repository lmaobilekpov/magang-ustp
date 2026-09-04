from django.db import models
from django.utils import timezone

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
    resi_jne = models.URLField(blank=True, null=True)
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
