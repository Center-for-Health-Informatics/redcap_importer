# Generated by Django 3.2.3 on 2021-05-17 17:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('redcap_importer', '0002_ignoreinstruments'),
    ]

    operations = [
        migrations.AddField(
            model_name='redcapconnection',
            name='partial_load',
            field=models.BooleanField(default=False, help_text='If True, only data for instruments marked "included" will be loaded.'),
        ),
        migrations.CreateModel(
            name='IncludeInstrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instrument_name', models.CharField(help_text='unique_name of the instrument to include', max_length=255)),
                ('connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.redcapconnection')),
            ],
        ),
    ]
