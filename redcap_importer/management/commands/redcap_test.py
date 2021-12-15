import json
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

import requests

from redcap_importer import models



class Command(BaseCommand):
    help = 'Populates tables for schema (Instrument and Event) but not Field definitions'

    def add_arguments(self, parser):
        parser.add_argument('connection_name')
        
    def run_request(self, content, oConnection, addl_options={}):
        addl_options['content'] = content
        addl_options['token'] = oConnection.get_api_token()
        addl_options['format'] = 'json'
        addl_options['returnFormat'] = 'json'
        return requests.post(oConnection.api_url.url, addl_options).json()

    def handle(self, *args, **options):
        connection_name = options['connection_name']
        oConnection = models.RedcapConnection.objects.get(unique_name=connection_name)
        print(oConnection.redcapproject)
        

        
        # get a list of all primary keys
        response = self.run_request('record', oConnection, {
            'fields': oConnection.primary_key_field,
        })
        pk_list = []
        for entry in response:
            pk = entry[oConnection.primary_key_field]
            if not pk in pk_list:
                pk_list.append(pk)
            
        print(pk_list)
            

        
    def insert_non_longitudinal(self, entry, oConnection):
#         print(entry[pk_field], 'not long')
#         print(entry['redcap_repeat_instrument'])
#         print(entry['redcap_repeat_instance'])
#         print()
        app_name = oConnection.django_app_name
        pk_field = oConnection.primary_key_field
        
        
        # get or create root
        ProjectRoot = apps.get_model(app_label=app_name, model_name='ProjectRoot')
        oRoot, created = ProjectRoot.objects.get_or_create(pk=entry[pk_field])
        # TO DO: set pk_label by looking up
        if entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.Instrument.objects.get(
                project=oConnection.redcapproject, unique_name=entry['redcap_repeat_instrument']
            )
            oInstrumentMetadata.create_instrument_record(entry, oRoot=oRoot)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.redcapproject.instrument_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                oInstrument.create_instrument_record(entry, oRoot=oRoot)
        
    def insert_longitudinal(self, entry, oConnection):
        app_name = oConnection.django_app_name
        pk_field = oConnection.primary_key_field
        
        
        # get or create root
        ProjectRoot = apps.get_model(app_label=app_name, model_name='ProjectRoot')
        oRoot, created = ProjectRoot.objects.get_or_create(pk=entry[pk_field])
        # TO DO: set pk_label by looking up
        oEventMetadata = models.Event.objects.get(
            project=oConnection.redcapproject, 
            unique_name=entry['redcap_event_name']
        )
        oEvent = oEventMetadata.get_or_create_event_record(oRoot)
        if entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.Instrument.objects.get(
                project=oConnection.redcapproject, unique_name=entry['redcap_repeat_instrument']
            )
            oInstrumentMetadata.create_instrument_record(entry, oEvent=oEvent)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.redcapproject.instrument_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                oInstrument.create_instrument_record(entry, oEvent=oEvent)
            

        
        
        
    
        
        
        
        
        
        
        
        
        
        
        