import json

from django.core.management.base import BaseCommand, CommandError

import requests

from redcap_import import models
# from redcap_import import helpers


class Command(BaseCommand):
    help = 'Populates tables for schema (Instrument and Event) but not Field definitions'

    def add_arguments(self, parser):
        parser.add_argument('connection_name')

    def handle(self, *args, **options):
        connection_name = options['connection_name']
        oProject = models.RedcapConnection.objects.get(name=connection_name).projectmetadata
        
        self.print_import_code()
        self.print_root_class(oProject)
        if oProject.is_longitudinal:
            self.print_event_class(oProject)
        for oInstrument in oProject.instrumentmetadata_set.all():
            self.print_instrument_class(oInstrument, oProject.is_longitudinal)
            self.print_lookup_tables(oInstrument)
        
        
        
    def print_blank_lines(self, count=1):
        for i in range(count):
            print()
        
    def print_import_code(self):
        print("from django.db import models")
        print("from redcap_import.abstract_models import AbstractProjectRoot, AbstractRedcapEvent")
        self.print_blank_lines(2)
        
    def print_root_class(self, oProject):
        print("class ProjectRoot(AbstractProjectRoot):")
        print("    {} = models.CharField(max_length=255, primary_key=True)".format(oProject.primary_key_field))
        print("    {}_display = models.TextField(blank=True, null=True)".format(oProject.primary_key_field))
        self.print_blank_lines(2)
        
    def print_event_class(self, oProject):
        print("class RedcapEvent(AbstractRedcapEvent):")
        print("    project_root = models.ForeignKey('ProjectRoot', on_delete=models.CASCADE)")
        print("    event_unique_name = models.TextField()")
        print("    event_label = models.TextField()")
        print("    arm_number = models.IntegerField()")
        print("    redcap_repeat_instance = models.IntegerField(blank=True, null=True)")
        self.print_blank_lines(2)
        
    def print_instrument_class(self, oInstrument, is_longitudinal):
        print( "class {}(models.Model):".format( oInstrument.get_django_model_name() ) )
        if is_longitudinal:
            print("    redcap_event = models.ForeignKey('RedcapEvent', on_delete=models.CASCADE)")
        else:
            print("    project_root = models.ForeignKey('ProjectRoot', on_delete=models.CASCADE)")
        print("    redcap_repeat_instance = models.IntegerField(blank=True, null=True)")
        for oField in oInstrument.fieldmetadata_set.exclude(is_many_to_many=True):
            print("    {} = models.{}(blank=True, null=True)".format(oField.get_django_field_name(), oField.django_data_type))
            if oField.get_display_lookup():
                print( "    {}_display_value = models.TextField(blank=True, null=True)".format( oField.get_django_field_name() ) )
        self.print_blank_lines(2)
        
    def print_lookup_tables(self, oInstrument):
        for oField in oInstrument.fieldmetadata_set.filter(is_many_to_many=True):
            print("class {}_{}_lookup(models.Model):".format(
                oInstrument.get_django_model_name(), oField.get_django_field_name()
            ))
            print("    {} = models.ForeignKey('{}', on_delete=models.CASCADE)".format(
                oInstrument.get_django_model_name(), oInstrument.get_django_model_name()
            ))
            print("    {} = models.TextField()".format(oField.get_django_field_name()))
            print("    {}_display_value = models.{}()".format(
                oField.get_django_field_name(), oField.django_data_type
            ))
            self.print_blank_lines(2)
        
        
        
        
        
        
        
        
        
        
        