import json
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps

import requests

from redcap_import import models

from pymongo import MongoClient



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
        print(oConnection.redcapproject)

        # get mongo collection
        mongo_client = MongoClient()
        mongo_db = mongo_client[settings.REDCAP_IMPORTER_MONGO_DB_NAME]
        mongo_collection = mongo_db[oConnection.django_app_name]

        #delete existing data
        count = mongo_collection.delete_many({}).deleted_count
        print('deleted from collection: {}'.format(count))

        # get a list of all primary keys
        response = self.run_request('record', oConnection, {
            'fields': oConnection.primary_key_field,
        })
        pk_list = []
        for entry in response:
            pk = entry[oConnection.primary_key_field]
            if not pk in pk_list:
                pk_list.append(pk)

        # do something for each primary key
        for pk in pk_list:
            response = self.run_request('record', oConnection, {
                'records[0]': pk,
            })

            if oConnection.redcapproject.is_longitudinal:
                for entry in response:
                    self.insert_longitudinal(entry, oConnection, mongo_collection)
            else:
                for entry in response:
                    self.insert_non_longitudinal(entry, oConnection, mongo_collection)
        oConnection.redcapproject.date_last_downloaded_data_mongo = datetime.datetime.now()
        oConnection.redcapproject.save()

    def insert_non_longitudinal(self, entry, oConnection, mongo_collection):

        pk_field = oConnection.primary_key_field

        # create new record or get existing record
        filter = {'record_id' : entry[pk_field]}
        doc = mongo_collection.find_one( filter )
        if not doc:
            doc = {}
            doc['record_id'] = entry[pk_field]
            doc['record_id_name'] = pk_field
            doc['instruments'] = {}

        # update instrument lists
        if entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.Instrument.objects.get(
                project=oConnection.redcapproject, unique_name=entry['redcap_repeat_instrument']
            )
            instrument_list_name = oInstrumentMetadata.get_django_model_name()
            if not instrument_list_name in doc['instruments']:
                doc['instruments'][instrument_list_name] = []
            instrument = oInstrumentMetadata.create_instrument_dict(entry)
            print('##########################################')
            if instrument:
                for key, val in instrument.items():
                    print(key, val)
                doc['instruments'][instrument_list_name].append(instrument)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrumentMetadata = oConnection.redcapproject.instrument_set.exclude(repeatable=True)
            for oInstrumentMetadata in qInstrumentMetadata:
                instrument_list_name = oInstrumentMetadata.get_django_model_name()
                if not instrument_list_name in doc['instruments']:
                    doc['instruments'][instrument_list_name] = []
                instrument = oInstrumentMetadata.create_instrument_dict(entry)
                print('##########################################')
                if instrument:
                    for key, val in instrument.items():
                        print(key, val)
                    doc['instruments'][instrument_list_name].append(instrument)

        # save document back to the database
        mongo_root.replace_one( filter, doc, upsert = True)

    def insert_longitudinal(self, entry, oConnection, mongo_root):
        pk_field = oConnection.primary_key_field

        # create new record or get existing record
        filter = {'record_id' : entry[pk_field]}
        doc = mongo_root.find_one( filter )
        if not doc:
            doc = {}
            doc['record_id'] = entry[pk_field]
            doc['record_id_name'] = pk_field
            doc['instruments'] = {}

        # update instrument lists
        if entry['redcap_repeat_instrument']:
            # repeat instrument, have 1 instrument to load
            oInstrumentMetadata = models.Instrument.objects.get(
                project=oConnection.redcapproject, unique_name=entry['redcap_repeat_instrument']
            )
            instrument_list_name = oInstrumentMetadata.get_django_model_name()
            if not instrument_list_name in doc['instruments']:
                doc[instrument_list_name] = []
            instrument = oInstrumentMetadata.create_instrument_dict(entry)
            print('##########################################')
            if instrument:
#                 for key, val in instrument.items():
#                     print(key, val)
                doc['instruments'][instrument_list_name].append(instrument)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrumentMetadata = oConnection.redcapproject.instrument_set.exclude(repeatable=True)
            for oInstrumentMetadata in qInstrumentMetadata:
                instrument_list_name = oInstrumentMetadata.get_django_model_name()
                if not instrument_list_name in doc['instruments']:
                    doc['instruments'][instrument_list_name] = []
                instrument = oInstrumentMetadata.create_instrument_dict(entry)
                print('##########################################')
                if instrument:
#                     for key, val in instrument.items():
#                         print(key, val)
                    doc['instruments'][instrument_list_name].append(instrument)

        # save document back to the database
        mongo_root.replace_one( filter, doc, upsert = True)