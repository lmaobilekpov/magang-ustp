from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dokumen', '0016_alter_dokumenkeluar_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiwayatStatusDokumenMasuk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Di Resepsionis', 'Di Resepsionis'), ('Sudah Diambil', 'Sudah Diambil')], max_length=50)),
                ('diubah_pada', models.DateTimeField(auto_now_add=True)),
                ('diubah_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='riwayat_dokumen_masuk', to=settings.AUTH_USER_MODEL)),
                ('dokumen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='riwayat_status', to='dokumen.dokumenmasuk')),
            ],
            options={
                'verbose_name': 'Riwayat Status Dokumen Masuk',
                'verbose_name_plural': 'Riwayat Status Dokumen Masuk',
                'ordering': ['-diubah_pada'],
            },
        ),
        migrations.CreateModel(
            name='RiwayatStatusDokumenKeluar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Menunggu Kurir', 'Menunggu Kurir'), ('Sudah Diserahkan ke JNE', 'Sudah Diserahkan ke JNE'), ('Paket Kembali', 'Paket Kembali')], max_length=50)),
                ('diubah_pada', models.DateTimeField(auto_now_add=True)),
                ('diubah_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='riwayat_dokumen_keluar', to=settings.AUTH_USER_MODEL)),
                ('dokumen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='riwayat_status', to='dokumen.dokumenkeluar')),
            ],
            options={
                'verbose_name': 'Riwayat Status Dokumen Keluar',
                'verbose_name_plural': 'Riwayat Status Dokumen Keluar',
                'ordering': ['-diubah_pada'],
            },
        ),
    ]
