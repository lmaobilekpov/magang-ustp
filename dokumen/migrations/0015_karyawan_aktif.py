from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dokumen', '0014_alter_karyawan_jabatan_alter_karyawan_kode_karyawan'),
    ]

    operations = [
        migrations.AddField(
            model_name='karyawan',
            name='aktif',
            field=models.BooleanField(default=True, verbose_name='Aktif'),
        ),
    ]
