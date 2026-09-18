from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .admin import DokumenKeluarAdmin, DokumenMasukAdmin
from .models import (
    Karyawan,
    DokumenMasuk,
    DokumenKeluar,
)


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
            karyawan_penerima=self.karyawan,
            status='Sudah Diambil',
            dob_pengambil=self.karyawan.tanggal_lahir,
        )
        dokumen.full_clean()
        dokumen.save()
        self.assertIsNotNone(dokumen.tanggal_diambil)

    def test_status_sudah_diambil_tanpa_dob_ditolak(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Sudah Diambil',
        )
        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_status_sudah_diambil_dengan_dob_salah_ditolak(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Sudah Diambil',
            dob_pengambil=date(1999, 5, 20),
        )
        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_waktu_pengambilan_lama_tetap_dipertahankan(self):
        waktu_awal = timezone.now()
        dokumen = DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Sudah Diambil',
            dob_pengambil=self.karyawan.tanggal_lahir,
        )
        dokumen.tanggal_diambil = waktu_awal
        dokumen.save(update_fields=['tanggal_diambil'])
        dokumen.status = 'Sudah Diambil'
        dokumen.dob_pengambil = self.karyawan.tanggal_lahir
        dokumen.save()
        self.assertAlmostEqual(dokumen.tanggal_diambil.timestamp(), waktu_awal.timestamp(), places=3)

    def test_status_di_resepsionis_tidak_memiliki_waktu_pengambilan(self):
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Di Resepsionis',
        )
        dokumen.full_clean()
        dokumen.save()
        self.assertIsNone(dokumen.tanggal_diambil)

    def test_legacy_null_di_resepsionis_valid(self):
        """Data lama tanpa karyawan_penerima + status Di Resepsionis harus tetap valid."""
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            nama_penerima='Siapa Saja', karyawan_penerima=None, status='Di Resepsionis',
        )
        dokumen.full_clean()

    def test_legacy_null_sudah_diambil_invalid(self):
        """Data lama tanpa karyawan_penerima + status Sudah Diambil harus ditolak."""
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            nama_penerima='Siapa Saja', karyawan_penerima=None, status='Sudah Diambil',
            dob_pengambil=date(2000, 1, 15),
        )
        with self.assertRaises(ValidationError):
            dokumen.full_clean()

    def test_migrasi_nama_unik_fk_terisi(self):
        """Simulasi data migration: nama unik harus otomatis cocok ke FK."""
        DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            nama_penerima='Budi Santoso', status='Di Resepsionis',
        )
        doc = DokumenMasuk.objects.filter(nama_penerima='Budi Santoso', karyawan_penerima__isnull=True).first()
        if doc:
            matches = Karyawan.objects.filter(nama_lengkap__iexact=doc.nama_penerima)
            if matches.count() == 1:
                doc.karyawan_penerima = matches.first()
                doc.save(update_fields=['karyawan_penerima'])
        doc.refresh_from_db()
        self.assertEqual(doc.karyawan_penerima, self.karyawan)

    def test_migrasi_nama_ambigu_fk_tetap_null(self):
        """Simulasi data migration: nama ambigu (>1 karyawan) harus tetap NULL."""
        Karyawan.objects.create(
            kode_karyawan='EMP099', nama_lengkap='Budi Santoso',
            jabatan='Manager', tanggal_lahir=date(1995, 5, 5),
        )
        doc = DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            nama_penerima='Budi Santoso', status='Di Resepsionis',
        )
        matches = Karyawan.objects.filter(nama_lengkap__iexact=doc.nama_penerima)
        if matches.count() == 1:
            doc.karyawan_penerima = matches.first()
            doc.save(update_fields=['karyawan_penerima'])
        doc.refresh_from_db()
        self.assertIsNone(doc.karyawan_penerima)

    def test_migrasi_nama_tidak_ditemukan_fk_tetap_null(self):
        """Simulasi data migration: nama yang tidak cocok harus tetap NULL."""
        doc = DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            nama_penerima='Nama Tidak Ada', status='Di Resepsionis',
        )
        matches = Karyawan.objects.filter(nama_lengkap__iexact=doc.nama_penerima)
        if matches.count() == 1:
            doc.karyawan_penerima = matches.first()
            doc.save(update_fields=['karyawan_penerima'])
        doc.refresh_from_db()
        self.assertIsNone(doc.karyawan_penerima)

    def test_nama_penerima_karyawan_nonaktif_ditolak(self):
        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Di Resepsionis',
        )
        with self.assertRaises(ValidationError):
            dokumen.full_clean()

    def test_dokumen_lama_tetap_bisa_diedit_setelah_karyawan_nonaktif(self):
        dokumen = DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Di Resepsionis',
        )
        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])
        dokumen.pengirim = 'Andi diperbarui'
        dokumen.full_clean()

    def test_nama_kembar_dengan_dob_berbeda(self):
        karyawan_2 = Karyawan.objects.create(
            kode_karyawan='EMP002',
            nama_lengkap='Budi Santoso',
            jabatan='Manager',
            tanggal_lahir=date(1995, 5, 5),
        )
        dokumen = DokumenMasuk.objects.create(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=karyawan_2, status='Di Resepsionis',
        )
        
        dokumen.status = 'Sudah Diambil'
        dokumen.dob_pengambil = date(1995, 5, 5)
        dokumen.full_clean()
        
        dokumen.dob_pengambil = date(2000, 1, 15)
        with self.assertRaises(ValidationError):
            dokumen.full_clean()


class DokumenKeluarTest(TestCase):
    def setUp(self):
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP001', nama_lengkap='Budi Santoso',
            jabatan='Staff', tanggal_lahir=date(2000, 1, 15),
        )

    def test_nomor_resi_internal_dibuat_otomatis(self):
        dokumen = DokumenKeluar.objects.create(
            nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen untuk dikirim',
        )
        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen.nomor_resi_internal, f'OUT-{today}-001')

    def test_status_sudah_diserahkan_ke_jne_tanpa_url_ditolak(self):
        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim', status='Sudah Diserahkan ke JNE',
        )
        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_nomor_resi_internal_berurutan(self):
        dokumen_1 = DokumenKeluar.objects.create(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen pertama')
        dokumen_2 = DokumenKeluar.objects.create(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen kedua')
        dokumen_3 = DokumenKeluar.objects.create(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen ketiga')
        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen_1.nomor_resi_internal, f'OUT-{today}-001')
        self.assertEqual(dokumen_2.nomor_resi_internal, f'OUT-{today}-002')
        self.assertEqual(dokumen_3.nomor_resi_internal, f'OUT-{today}-003')

    def test_nomor_resi_internal_hari_berikutnya_mulai_dari_001(self):
        tanggal_kemarin = timezone.now().date() - timezone.timedelta(days=1)
        dokumen_lama = DokumenKeluar(
            nomor_resi_internal=f'OUT-{tanggal_kemarin.strftime("%Y%m%d")}-007',
            tanggal_terima=tanggal_kemarin, nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen kemarin',
        )
        dokumen_lama.save(force_insert=True)
        dokumen_baru = DokumenKeluar.objects.create(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen hari ini')
        today = timezone.now().strftime('%Y%m%d')
        self.assertEqual(dokumen_baru.nomor_resi_internal, f'OUT-{today}-001')

    def test_nama_pengirim_terdaftar_diterima(self):
        dokumen = DokumenKeluar(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen untuk dikirim')
        dokumen.full_clean()
        self.assertEqual(dokumen.nama_pengirim, self.karyawan.nama_lengkap)

    def test_nama_pengirim_tidak_terdaftar_ditolak(self):
        dokumen = DokumenKeluar(nama_pengirim='Nama Ngawur', deskripsi='Dokumen untuk dikirim')
        with self.assertRaises(Exception):
            dokumen.full_clean()

    def test_nama_pengirim_karyawan_nonaktif_ditolak(self):
        self.karyawan.aktif = False
        self.karyawan.save(update_fields=['aktif'])
        dokumen = DokumenKeluar(nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen untuk dikirim')
        with self.assertRaises(ValidationError):
            dokumen.full_clean()

    def test_paket_kembali_tidak_bisa_langsung_dibuat(self):
        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap, deskripsi='Dokumen untuk dikirim',
            status='Paket Kembali', resi_jne='https://jne.co.id/tracking/ABC123',
        )
        with self.assertRaises(ValidationError):
            dokumen.full_clean()


class StatusHistoryTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='resepsionis', password='password123')
        self.other_user = User.objects.create_user(username='operator2', password='password123')
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP010', nama_lengkap='Citra Lestari',
            jabatan='Staff', tanggal_lahir=date(2001, 2, 3),
        )
        self.factory = RequestFactory()

    def test_dokumen_masuk_mencatat_status_awal_dan_perubahan(self):
        request = self.factory.post('/admin/dokumen/dokumenmasuk/add/')
        request.user = self.user
        admin_model = DokumenMasukAdmin(DokumenMasuk, admin.site)
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Di Resepsionis',
        )
        admin_model.save_model(request, dokumen, None, False)
        dokumen.status = 'Sudah Diambil'
        dokumen.dob_pengambil = self.karyawan.tanggal_lahir
        admin_model.save_model(request, dokumen, None, True)
        riwayat = list(dokumen.riwayat_status.order_by('diubah_pada'))
        self.assertEqual([item.status for item in riwayat], ['Di Resepsionis', 'Sudah Diambil'])
        self.assertEqual(riwayat[0].diubah_oleh, self.user)
        self.assertEqual(riwayat[1].diubah_oleh, self.user)

    def test_dokumen_masuk_tidak_menambah_histori_jika_status_tetap(self):
        request = self.factory.post('/admin/dokumen/dokumenmasuk/change/')
        request.user = self.user
        admin_model = DokumenMasukAdmin(DokumenMasuk, admin.site)
        dokumen = DokumenMasuk(
            kategori='Paket Pribadi', jenis_pengirim='Non-PT', pengirim='Andi',
            karyawan_penerima=self.karyawan, status='Di Resepsionis',
        )
        admin_model.save_model(request, dokumen, None, False)
        self.assertEqual(dokumen.riwayat_status.count(), 1)
        dokumen.pengirim = 'Andi Diperbarui'
        admin_model.save_model(request, dokumen, None, True)
        self.assertEqual(dokumen.riwayat_status.count(), 1)

    def test_dokumen_keluar_mencatat_pengubah_status(self):
        request = self.factory.post('/admin/dokumen/dokumenkeluar/add/')
        request.user = self.user
        admin_model = DokumenKeluarAdmin(DokumenKeluar, admin.site)
        dokumen = DokumenKeluar(
            nama_pengirim=self.karyawan.nama_lengkap,
            deskripsi='Dokumen untuk dikirim', status='Menunggu Kurir',
        )
        admin_model.save_model(request, dokumen, None, False)
        request.user = self.other_user
        dokumen.status = 'Sudah Diserahkan ke JNE'
        dokumen.resi_jne = 'https://jne.co.id/tracking/ABC123'
        admin_model.save_model(request, dokumen, None, True)
        riwayat = list(dokumen.riwayat_status.order_by('diubah_pada'))
        self.assertEqual([item.status for item in riwayat], ['Menunggu Kurir', 'Sudah Diserahkan ke JNE'])
        self.assertEqual(riwayat[0].diubah_oleh, self.user)
        self.assertEqual(riwayat[1].diubah_oleh, self.other_user)


class PortalKaryawanTest(TestCase):
    def setUp(self):
        self.karyawan = Karyawan.objects.create(
            kode_karyawan='EMP002', nama_lengkap='Siti Aminah',
            jabatan='Staff', tanggal_lahir=date(1999, 5, 20),
        )

    def test_verifikasi_dob_benar_menampilkan_portal(self):
        response = self.client.post(reverse('lacak_dokumen'), {'tanggal_lahir': '1999-05-20'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.karyawan.nama_lengkap)

    def test_verifikasi_dob_salah_ditolak(self):
        response = self.client.post(reverse('lacak_dokumen'), {'tanggal_lahir': '1999-05-21'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tanggal lahir tidak ditemukan')

    def test_verifikasi_dob_ganda_ditolak(self):
        Karyawan.objects.create(
            kode_karyawan='EMP003', nama_lengkap='Andi Pratama',
            jabatan='Staff', tanggal_lahir=self.karyawan.tanggal_lahir,
        )
        response = self.client.post(reverse('lacak_dokumen'), {'tanggal_lahir': '1999-05-20'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lebih dari satu karyawan')
