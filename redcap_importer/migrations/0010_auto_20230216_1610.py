# Generated by Django 3.2.10 on 2023-02-16 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('redcap_importer', '0009_auto_20230214_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='etllog',
            name='direction',
            field=models.CharField(blank=True, choices=[('download', 'download from REDCap'), ('upload', 'upload to REDCap')], max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='etllog',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
