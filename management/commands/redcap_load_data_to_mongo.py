import json
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps

import requests

from redcap_importer import models

from pymongo import MongoClient



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
        oConnection = models.RedcapConnection.objects.get(name=connection_name)
        print(oConnection.unique_name)

        # get mongo collection
        con = settings.REDCAP_IMPORTER_MONGO_CONNECTION_SETTINGS
        mongo_client = MongoClient(**con)
        mongo_db = mongo_client[settings.REDCAP_IMPORTER_MONGO_DB_NAME]
        mongo_collection = mongo_db[oConnection.unique_name]

        #delete existing data
        count = mongo_collection.delete_many({}).deleted_count
        print('deleted from collection: {}'.format(count))

        # get a list of all primary keys
        response = self.run_request('record', oConnection, {
            'fields': oConnection.projectmetadata.primary_key_field,
        })
        pk_list = []
        for entry in response:
            pk = entry[oConnection.projectmetadata.primary_key_field]
            if not pk in pk_list:
                pk_list.append(pk)

        # do something for each primary key
        for pk in pk_list:
            response = self.run_request('record', oConnection, {
                'records[0]': pk,
            })

            if oConnection.projectmetadata.is_longitudinal:
                for entry in response:
                    self.insert_longitudinal(entry, oConnection, mongo_collection)
            else:
                for entry in response:
                    self.insert_non_longitudinal(entry, oConnection, mongo_collection)
        oConnection.projectmetadata.date_last_downloaded_data_mongo = datetime.datetime.now()
        oConnection.projectmetadata.save()

    def insert_non_longitudinal(self, entry, oConnection, mongo_collection):

        pk_field = oConnection.projectmetadata.primary_key_field

        # create new record or get existing record
        filter = {'record_id' : entry[pk_field]}
        doc = mongo_collection.find_one( filter )
        if not doc:
            doc = {}
            doc['record_id'] = entry[pk_field]
            doc['record_id_name'] = pk_field
            doc['instruments'] = {}

        # update instrument lists
        doc = update_instrument_lists(self, entry, doc, oConnection)

        # save document back to the database
        mongo_root.replace_one( filter, doc, upsert = True)
        
    def insert_longitudinal(self, entry, oConnection, mongo_root):
        pk_field = oConnection.projectmetadata.primary_key_field

        # create new record or get existing record
        filter = {'record_id' : entry[pk_field]}
        doc = mongo_root.find_one( filter )
        if not doc:
            doc = {}
            doc['record_id'] = entry[pk_field]
            doc['record_id_name'] = pk_field
            doc['instruments'] = {}
            doc['events'] = {}

        # update instrument lists
        # doc = self.update_instrument_lists(entry, doc, oConnection)
        doc = self.update_event_lists(entry, doc, oConnection)

        # save document back to the database
        mongo_root.replace_one( filter, doc, upsert = True)
        
    def update_event_lists(self, entry, doc, oConnection):
        oEventMetadata = models.EventMetadata.objects.get(
            project=oConnection.projectmetadata, 
            unique_name=entry['redcap_event_name']
        )
        event_name = oEventMetadata.unique_name
        
        # get or create the event subdocument to use
        if oEventMetadata.repeatable:
            if not event_name in doc['events']:
                doc['events'][event_name] = []
                event_subdoc = doc['events'][event_name].append()
            else:
                event_subdoc = next(
                    (item for item in doc['events'][event_name] if item['redcap_repeat_instance'] == entry['redcap_repeat_instance']), 
                    {
                        'redcap_repeat_instance' : entry['redcap_repeat_instance'],
                        'event_label' : oEventMetadata.label,
                        'arm_number' : oEventMetadata.arm.arm_number,
                        'arm_name' : oEventMetadata.arm.arm_name,
                    }
                )               
        else: # event not repeatable
            if not event_name in doc['events']:
                doc['events'][event_name] = {
                    'event_label' : oEventMetadata.label,
                    'arm_number' : oEventMetadata.arm.arm_number,
                    'arm_name' : oEventMetadata.arm.arm_name,
                }
            event_subdoc = doc['events'][event_name]
                
        if not 'instruments' in event_subdoc:
            event_subdoc['instruments'] = {}
        
        # now we can add instrument data to our event dict        
        if entry['redcap_repeat_instrument'] and not oEventMetadata.repeatable:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=entry['redcap_repeat_instrument']
            )
            instrument_list_name = oInstrumentMetadata.get_django_model_name()
            if not instrument_list_name in event_subdoc['instruments']:
                event_subdoc['instruments'][instrument_list_name] = []
            instrument = oInstrumentMetadata.create_instrument_dict(entry)
            if instrument:
                event_subdoc['instruments'][instrument_list_name].append(instrument)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrumentMetadata = models.InstrumentMetadata.objects.filter(eventinstrumentmetadata__event=oEventMetadata)
            for oInstrumentMetadata in qInstrumentMetadata:
                instrument_list_name = oInstrumentMetadata.get_django_model_name()
                if not instrument_list_name in event_subdoc['instruments']:
                    event_subdoc['instruments'][instrument_list_name] = []
                instrument = oInstrumentMetadata.create_instrument_dict(entry)
                if instrument:
                    event_subdoc['instruments'][instrument_list_name].append(instrument)        
        
        return doc
        
    ##################################################################    
        
    def update_instrument_lists(self, entry, doc, oConnection):
        if entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=entry['redcap_repeat_instrument']
            )
            instrument_list_name = oInstrumentMetadata.get_django_model_name()
            if not instrument_list_name in doc['instruments']:
                doc['instruments'][instrument_list_name] = []
            instrument = oInstrumentMetadata.create_instrument_dict(entry)
            if instrument:
                doc['instruments'][instrument_list_name].append(instrument)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrumentMetadata = oConnection.projectmetadata.instrumentmetadata_set.exclude(repeatable=True)
            for oInstrumentMetadata in qInstrumentMetadata:
                instrument_list_name = oInstrumentMetadata.get_django_model_name()
                if not instrument_list_name in doc['instruments']:
                    doc['instruments'][instrument_list_name] = []
                instrument = oInstrumentMetadata.create_instrument_dict(entry)
                if instrument:
                    doc['instruments'][instrument_list_name].append(instrument)
        return doc


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        