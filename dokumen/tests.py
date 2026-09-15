from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Karyawan, DokumenMasuk, DokumenKeluar


class DokumenMasukTest(TestCase):
    def setUp(self):
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP001',
            nama_lengkap='Budi Santoso',
            jabatan='Staff',
            tanggal_lahir=date(2000, 1, 15),
        )

    def test_status_sudah_diambil_mengisi_waktu_pengambilan(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Sudah Diambil',
            dob_pengambil=self.karyawan.tanggal_lahir,
        )

        dokumen.full_clean()
        dokumen.save()

        self.assertIsNotNone(dokumen.tanggal_diambil)

    def test_status_sudah_diambil_tanpa_dob_ditolak(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Sudah Diambil',
        )

        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_status_sudah_diambil_dengan_dob_salah_ditolak(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Sudah Diambil',
            dob_pengambil=date(1999, 5, 20),
        )

        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_waktu_pengambilan_lama_tetap_dipertahankan(self):
        waktu_awal = timezone.now()
        dokumen = DokumenMasuk.objects.create(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Sudah Diambil',
            dob_pengambil=self.karyawan.tanggal_lahir,
        )
        dokumen.tanggal_diambil = waktu_awal
        dokumen.save(update_fields=['tanggal_diambil'])

        dokumen.status = 'Sudah Diambil'
        dokumen.dob_pengambil = self.karyawan.tanggal_lahir
        dokumen.save()

        self.assertAlmostEqual(
            dokumen.tanggal_diambil.timestamp(),
            waktu_awal.timestamp(),
            places=3,
        )

    def test_status_di_resepsionis_tidak_memiliki_waktu_pengambilan(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Di Resepsionis',
        )

        dokumen.full_clean()
        dokumen.save()

        self.assertIsNone(dokumen.tanggal_diambil)

    def test_nama_penerima_tidak_terdaftar_ditolak(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima='Nama Ngawur',
            status='Di Resepsionis',
        )

        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_nama_penerima_karyawan_nonaktif_ditolak(self):
        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])

        dokumen = DokumenMasuk(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Di Resepsionis',
        )

        with self.assertRaises(ValidationError):
            dokumen.full_clean()

    def test_dokumen_lama_tetap_bisa_diedit_setelah_karyawan_nonaktif(self):
        dokumen = DokumenMasuk.objects.create(
            kategori='Paket Pribadi',
            jenis_pengirim='Non-PT',
            pengirim='Andi',
            nama_penerima=self.karyawan.nama_lengkap,
            status='Di Resepsionis',
        )

        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])

        dokumen.pengirim = 'Andi diperbarui'
        dokumen.full_clean()


class DokumenKeluarTest(TestCase):
    def setUp(self):
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP001',
            nama_lengkap='Budi Santoso',
            jabatan='Staff',
            tanggal_lahir=date(2000, 1, 15),
        )

    def test_nomor_resi_internal_dibuat_otomatis(self):
        dokumen = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim',
        )

        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen.nomor_resi_internal, f'OUT-{today}-001')

    def test_status_sudah_diserahkan_ke_jne_tanpa_url_ditolak(self):
        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim',
            status='Sudah Diserahkan ke JNE',
        )

        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_nomor_resi_internal_berurutan(self):
        dokumen_1 = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen pertama',
        )
        dokumen_2 = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen kedua',
        )
        dokumen_3 = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen ketiga',
        )

        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen_1.nomor_resi_internal, f'OUT-{today}-001')
        self.assertEqual(dokumen_2.nomor_resi_internal, f'OUT-{today}-002')
        self.assertEqual(dokumen_3.nomor_resi_internal, f'OUT-{today}-003')

    def test_nomor_resi_internal_hari_berikutnya_mulai_dari_001(self):
        tanggal_kemarin = timezone.now().date() - timezone.timedelta(days=1)
        dokumen_lama = DokumenKeluar(
            nomor_resi_internal=f'OUT-{tanggal_kemarin.strftime("%Y%m%d")}-007',
            tanggal_terima=tanggal_kemarin,
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen kemarin',
        )
        dokumen_lama.save(force_insert=True)

        dokumen_baru = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen hari ini',
        )

        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen_baru.nomor_resi_internal, f'OUT-{today}-001')

    def test_nama_pengirim_terdaftar_diterima(self):
        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim',
        )

        dokumen.full_clean()
        self.assertEqual(dokumen.nama_pengirim, self.karyawan.nama_lengkap)

    def test_nama_pengirim_tidak_terdaftar_ditolak(self):
        dokumen = DokumenKeluar(
            nama_pengirim='Nama Ngawur',
            deskripsi='Dokumen untuk dikirim',
        )

        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_nama_pengirim_karyawan_nonaktif_ditolak(self):
        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])

        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim',
        )

        with self.assertRaises(ValidationError):
            dokumen.full_clean()


class PortalKaryawanTest(TestCase):
    def setUp(self):
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP002',
            nama_lengkap='Siti Aminah',
            jabatan='Staff',
            tanggal_lahir=date(1999, 5, 20),
        )

    def test_verifikasi_dob_benar_menampilkan_portal(self):
        response = self.client.post(
            reverse('lacak_dokumen'),
            {'tanggal_lahir': '1999-05-20'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.karyawan.nama_lengkap)

    def test_verifikasi_dob_salah_ditolak(self):
        response = self.client.post(
            reverse('lacak_dokumen'),
            {'tanggal_lahir': '1999-05-21'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tanggal Lahir tidak ditemukan')

    def test_verifikasi_dob_ganda_ditolak(self):
        Karyawan.objects.create(
            kode_karyawan='EMP003',
            nama_lengkap='Andi Pratama',
            jabatan='Staff',
            tanggal_lahir=self.karyawan.tanggal_lahir,
        )

        response = self.client.post(
            reverse('lacak_dokumen'),
            {'tanggal_lahir': '1999-05-20'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lebih dari satu karyawan')
