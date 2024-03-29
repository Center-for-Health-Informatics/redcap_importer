# Generated by Django 3.2.3 on 2021-05-17 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('redcap_importer', '0003_auto_20210517_1752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='redcapconnection',
            name='partial_load',
            field=models.BooleanField(default=False, help_text='If True, only instruments in IncludeInstrument list will be loaded.'),
        ),
        migrations.DeleteModel(
            name='IgnoreInstruments',
        ),
    ]
