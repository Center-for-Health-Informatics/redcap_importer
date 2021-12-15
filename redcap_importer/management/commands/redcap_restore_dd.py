from django.core.management.base import BaseCommand
from django.core.management import call_command

from redcap_importer import models
from redcap_importer import redcap_importer_settings


class Command(BaseCommand):
    help = "Overwrites chiron config models with output from chiron_copy_config."

    def print_out(self, *args):
        """ A wrapper for self.stdout.write() that converts anything into a string """
        strings = []
        for arg in args:
            strings.append(str(arg))
        self.stdout.write(",".join(strings))

    def print_err(self, *args):
        """ A wrapper for self.stderr.write() that converts anything into a string """
        strings = []
        for arg in args:
            strings.append(str(arg))
        self.stderr.write(",".join(strings))

    def add_arguments(self, parser):
        # parser.add_argument('path_to_fixture')
        pass

    def handle(self, *args, **options):

        fixture_path = redcap_importer_settings.REDCAP_DATA_DICT_FIXTURE_PATH

        models.FieldMetadata.objects.all().delete()
        models.EventInstrumentMetadata.objects.all().delete()
        models.InstrumentMetadata.objects.all().delete()
        models.EventMetadata.objects.all().delete()
        models.ArmMetadata.objects.all().delete()
        models.ProjectMetadata.objects.all().delete()
        models.IncludeInstrument.objects.all().delete()
        models.RedcapConnection.objects.all().delete()
        models.RedcapApiUrl.objects.all().delete()

        call_command(
            "loaddata", fixture_path,
        )
