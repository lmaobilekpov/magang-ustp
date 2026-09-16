from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dokumen', '0016_alter_dokumenkeluar_status'),
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
