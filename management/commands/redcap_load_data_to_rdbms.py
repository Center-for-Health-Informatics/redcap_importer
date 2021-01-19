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
        addl_options['token'] = oConnection.api_token
        addl_options['format'] = 'json'
        addl_options['returnFormat'] = 'json'
        return requests.post(oConnection.api_url.url, addl_options).json()

    def handle(self, *args, **options):
        connection_name = options['connection_name']
        oConnection = models.RedcapConnection.objects.get(name=connection_name)
        print(oConnection.projectmetadata)
        
        #delete existing data
        app_name = oConnection.unique_name
        pk_field = oConnection.projectmetadata.primary_key_field
        ProjectRoot = apps.get_model(app_label=app_name, model_name='ProjectRoot')
        for oRoot in ProjectRoot.objects.all():
            oRoot.delete()
        
        # get a list of all primary keys
        response = self.run_request('record', oConnection, {
            'fields': oConnection.projectmetadata.primary_key_field,
        })
        pk_list = []
        for entry in response:
            pk = entry[oConnection.projectmetadata.primary_key_field]
            if not pk in pk_list:
                pk_list.append(pk)
            
        for pk in pk_list:
            response = self.run_request('record', oConnection, {
                'records[0]': pk,
            })
            
            if oConnection.projectmetadata.is_longitudinal:
                for entry in response:
                    self.insert_longitudinal(entry, oConnection)
            else:
                for entry in response:
                    self.insert_non_longitudinal(entry, oConnection)
        oConnection.projectmetadata.date_last_downloaded_data = datetime.datetime.now()
        oConnection.projectmetadata.save()
        
    def insert_non_longitudinal(self, entry, oConnection):
#         print(entry[pk_field], 'not long')
#         print(entry['redcap_repeat_instrument'])
#         print(entry['redcap_repeat_instance'])
#         print()
        app_name = oConnection.unique_name
        pk_field = oConnection.projectmetadata.primary_key_field
        
        
        # get or create root
        ProjectRoot = apps.get_model(app_label=app_name, model_name='ProjectRoot')
        oRoot, created = ProjectRoot.objects.get_or_create(pk=entry[pk_field])
        # TO DO: set pk_label by looking up
        if 'redcap_repeat_instrument' in entry and entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=entry['redcap_repeat_instrument']
            )
            oInstrumentMetadata.create_instrument_record(entry, oRoot=oRoot)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.projectmetadata.instrumentmetadata_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                oInstrument.create_instrument_record(entry, oRoot=oRoot)
        
    def insert_longitudinal(self, entry, oConnection):
        app_name = oConnection.unique_name
        pk_field = oConnection.projectmetadata.primary_key_field
        
        
        # get or create root
        ProjectRoot = apps.get_model(app_label=app_name, model_name='ProjectRoot')
        oRoot, created = ProjectRoot.objects.get_or_create(pk=entry[pk_field])
        # TO DO: set pk_label by looking up

        oEventMetadata = models.EventMetadata.objects.get(
            project=oConnection.projectmetadata, 
            unique_name=entry['redcap_event_name']
        )
        oEvent = oEventMetadata.get_or_create_event_record(oRoot)

        if 'redcap_repeat_instrument' in entry and entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=entry['redcap_repeat_instrument']
            )
            oInstrumentMetadata.create_instrument_record(entry, oEvent=oEvent)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.projectmetadata.instrumentmetadata_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                oInstrument.create_instrument_record(entry, oEvent=oEvent)
            

        
        
        
    
        
        
        
        
        
        
        
        
        
        
        