# Generated by Django 2.1.15 on 2019-12-09 14:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArmMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arm_number', models.IntegerField()),
                ('arm_name', models.TextField()),
            ],
            options={
                'ordering': ('arm_number',),
            },
        ),
        migrations.CreateModel(
            name='EventInstrumentMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('repeatable', models.BooleanField(default=False, help_text='should be false if associated event is repeatable')),
                ('ordering', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='EventMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_name', models.CharField(help_text='unique for RedcapProject', max_length=255)),
                ('label', models.TextField()),
                ('ordering', models.IntegerField()),
                ('repeatable', models.BooleanField(default=False)),
                ('arm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.ArmMetadata')),
            ],
            options={
                'ordering': ('ordering',),
            },
        ),
        migrations.CreateModel(
            name='FieldMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('django_data_type', models.CharField(help_text='ex. DateField, TextField', max_length=120)),
                ('unique_name', models.CharField(help_text='unique for Instrument', max_length=255)),
                ('django_field_name', models.CharField(blank=True, help_text='set if different from unique_name', max_length=255, null=True)),
                ('label', models.TextField()),
                ('ordering', models.IntegerField()),
                ('field_display_lookup', models.TextField(default='{}', help_text='If set, creates a second field [field_name]_display and attempts to populate it with lookup val')),
                ('is_many_to_many', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['ordering'],
            },
        ),
        migrations.CreateModel(
            name='InstrumentMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_name', models.CharField(help_text='unique for RedcapProject', max_length=255)),
                ('django_model_name', models.CharField(blank=True, help_text='set if different from unique_name', max_length=255, null=True)),
                ('label', models.TextField()),
                ('repeatable', models.BooleanField(default=False, help_text='this will be ignored for longitudinal studies, use EventInstrument.repeatable instead')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_title', models.CharField(max_length=255)),
                ('is_longitudinal', models.BooleanField()),
                ('has_multiple_arms', models.BooleanField(default=False)),
                ('date_last_updated_metadata', models.DateTimeField(auto_now_add=True)),
                ('date_last_downloaded_data', models.DateTimeField(blank=True, null=True)),
                ('date_last_downloaded_data_mongo', models.DateTimeField(blank=True, null=True)),
                ('date_last_uploaded_data', models.DateTimeField(blank=True, null=True)),
                ('primary_key_field', models.CharField(help_text='ex. record_id, study_id, etc.', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='RedcapApiUrl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('url', models.URLField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='RedcapConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('unique_name', models.SlugField(help_text='This will be the name of the Django app or Mongo collection', unique=True)),
                ('api_token', models.CharField(max_length=255)),
                ('api_url', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='redcap_importer.RedcapApiUrl')),
            ],
        ),
        migrations.AddField(
            model_name='projectmetadata',
            name='connection',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.RedcapConnection'),
        ),
        migrations.AddField(
            model_name='instrumentmetadata',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.ProjectMetadata'),
        ),
        migrations.AddField(
            model_name='fieldmetadata',
            name='instrument',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.InstrumentMetadata'),
        ),
        migrations.AddField(
            model_name='eventmetadata',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.ProjectMetadata'),
        ),
        migrations.AddField(
            model_name='eventinstrumentmetadata',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.EventMetadata'),
        ),
        migrations.AddField(
            model_name='eventinstrumentmetadata',
            name='instrument',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.InstrumentMetadata'),
        ),
        migrations.AddField(
            model_name='armmetadata',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redcap_importer.ProjectMetadata'),
        ),
        migrations.AlterUniqueTogether(
            name='instrumentmetadata',
            unique_together={('project', 'unique_name')},
        ),
        migrations.AlterUniqueTogether(
            name='eventmetadata',
            unique_together={('project', 'unique_name')},
        ),
        migrations.AlterUniqueTogether(
            name='armmetadata',
            unique_together={('project', 'arm_number')},
        ),
    ]
