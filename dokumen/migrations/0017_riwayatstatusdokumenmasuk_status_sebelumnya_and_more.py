from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dokumen', '0017_riwayat_status_dokumen'),
    ]

    operations = [
        migrations.AddField(
            model_name='riwayatstatusdokumenmasuk',
            name='status_sebelumnya',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Status Sebelumnya'),
        ),
        migrations.AddField(
            model_name='riwayatstatusdokumenkeluar',
            name='status_sebelumnya',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Status Sebelumnya'),
        ),
    ]
