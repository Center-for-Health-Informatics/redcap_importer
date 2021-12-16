import json

from django.core.management.base import BaseCommand, CommandError

import requests

from redcap_importer import models
# from redcap_importer import helpers


class Command(BaseCommand):
    help = 'Populates tables for schema (Instrument and Event) but not Field definitions'

    def add_arguments(self, parser):
        parser.add_argument('connection_name')

    def handle(self, *args, **options):
        connection_name = options['connection_name']
        oProject = models.RedcapConnection.objects.get(unique_name=connection_name).projectmetadata

        # save all the lines to self.output and print everything at the end to allow more control over how things print
        self.output = []
        
        self.print_import_code()
        self.print_root_class(oProject)
        if oProject.is_longitudinal:
            self.print_event_class(oProject)
        for oInstrument in oProject.instrumentmetadata_set.all():
            self.print_instrument_class(oInstrument, oProject.is_longitudinal)
            self.print_lookup_tables(oInstrument)

        print("\n".join(self.output))
        
        
        
    def print_blank_lines(self, count=1):
        for i in range(count):
            self.output.append("")
        
    def print_import_code(self):
        self.output.append("from django.db import models")
        self.output.append("from redcap_importer.abstract_models import AbstractProjectRoot, AbstractRedcapEvent")
        self.print_blank_lines(2)
        
    def print_root_class(self, oProject):
        self.output.append("class ProjectRoot(AbstractProjectRoot):")
        self.output.append("    {} = models.CharField(max_length=255, primary_key=True)".format(oProject.primary_key_field))
        self.output.append("    {}_display = models.TextField(blank=True, null=True)".format(oProject.primary_key_field))
        self.print_blank_lines(2)
        
    def print_event_class(self, oProject):
        self.output.append("class RedcapEvent(AbstractRedcapEvent):")
        self.output.append("    project_root = models.ForeignKey('ProjectRoot', on_delete=models.CASCADE)")
        self.output.append("    event_unique_name = models.TextField()")
        self.output.append("    event_label = models.TextField()")
        self.output.append("    arm_number = models.IntegerField()")
        self.output.append("    redcap_repeat_instance = models.IntegerField(blank=True, null=True)")
        self.print_blank_lines(2)
        
    def print_instrument_class(self, oInstrument, is_longitudinal):
        self.output.append( "class {}(models.Model):".format( oInstrument.get_django_model_name() ) )
        if is_longitudinal:
            self.output.append("    redcap_event = models.ForeignKey('RedcapEvent', on_delete=models.CASCADE)")
        else:
            self.output.append("    project_root = models.ForeignKey('ProjectRoot', on_delete=models.CASCADE)")
        self.output.append("    redcap_repeat_instance = models.IntegerField(blank=True, null=True)")
        for oField in oInstrument.fieldmetadata_set.exclude(is_many_to_many=True):
            self.output.append("    {} = models.{}(blank=True, null=True)".format(oField.get_django_field_name(), oField.django_data_type))
            if oField.get_display_lookup():
                self.output.append( "    {}_display_value = models.TextField(blank=True, null=True)".format( oField.get_django_field_name() ) )
        self.print_blank_lines(2)
        
    def print_lookup_tables(self, oInstrument):
        for oField in oInstrument.fieldmetadata_set.filter(is_many_to_many=True):
            self.output.append("class {}_{}_lookup(models.Model):".format(
                oInstrument.get_django_model_name(), oField.get_django_field_name()
            ))
            self.output.append("    {} = models.ForeignKey('{}', on_delete=models.CASCADE)".format(
                oInstrument.get_django_model_name(), oInstrument.get_django_model_name()
            ))
            self.output.append("    {} = models.TextField()".format(oField.get_django_field_name()))
            self.output.append("    {}_display_value = models.{}()".format(
                oField.get_django_field_name(), oField.django_data_type
            ))
            self.print_blank_lines(2)
        
        
        
        
        
        
        
        
        
        
        