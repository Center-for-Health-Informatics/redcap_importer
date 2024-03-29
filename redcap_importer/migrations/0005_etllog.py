# Generated by Django 3.2.3 on 2021-05-18 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('redcap_importer', '0004_auto_20210517_1829'),
    ]

    operations = [
        migrations.CreateModel(
            name='EtlLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('redcap_project', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('ETL started', 'ETL started'), ('ETL completed', 'ETL completed')], max_length=20)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('instruments_loaded', models.TextField(blank=True, null=True)),
                ('query_count', models.IntegerField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
    ]
