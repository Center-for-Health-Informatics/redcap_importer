from django.core.management.base import BaseCommand
from django.core.management import call_command

from redcap_importer import redcap_importer_settings


class Command(BaseCommand):
    help = "Backs up all redcap connections and the loaded redcap data dictionaries."

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
        pass

    def handle(self, *args, **options):

        output_path = redcap_importer_settings.REDCAP_DATA_DICT_FIXTURE_PATH

        # create a backup of all Root, Category, Concept, SourceCollection,
        # AutoImportedFields
        call_command(
            "dumpdata",
            "redcap_importer.RedcapApiUrl",
            "redcap_importer.RedcapConnection",
            "redcap_importer.IncludeInstrument",
            "redcap_importer.ProjectMetadata",
            "redcap_importer.ArmMetadata",
            "redcap_importer.EventMetadata",
            "redcap_importer.InstrumentMetadata",
            "redcap_importer.EventInstrumentMetadata",
            "redcap_importer.FieldMetadata",
            indent=4,
            output=output_path,
        )
