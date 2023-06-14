import json
import datetime
from io import StringIO
import sys

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

import requests

from redcap_importer import models



class Command(BaseCommand):
    help = 'Populates tables for schema (Instrument and Event) but not Field definitions'

    def __init__(self, *args, **kwargs):
        self.query_count = 0
        self.log_comments = []  # a list of comments to save with the ETL log
        super().__init__(*args, **kwargs)

    def print_out(self, *args, **kwargs):
        """A wrapper for self.stdout.write() that converts anything into a string"""
        strings = []
        for arg in args:
            strings.append(str(arg))
        ouput = ",".join(strings)
        if "log" in kwargs and kwargs["log"]:
            self.log_comments.append(ouput)
        self.stdout.write(ouput)

    def start_capture_stdout(self):
        self.captured_stdout = []
        self.original_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

    def finish_capture_stdout(self, log=True):
        sys.stdout = self.original_stdout
        for line in self.captured_stdout:
            self.print_out(line, log)

    def add_arguments(self, parser):
        parser.add_argument('connection_name')
        
    def run_request(self, content, oConnection, addl_options={}):
        addl_options['content'] = content
        addl_options['token'] = oConnection.get_api_token()
        addl_options['format'] = 'json'
        addl_options['returnFormat'] = 'json'
        self.query_count += 1
        response = requests.post(oConnection.api_url.url, addl_options)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request to REDCap API for {oConnection.projectmetadata} failed\nResponse: {response.json()}")

    def handle(self, *args, **options):
        connection_name = options['connection_name']
        oConnection = models.RedcapConnection.objects.get(unique_name=connection_name)
        self.print_out(oConnection.projectmetadata, log=True)
        self.query_count = 0

        self.oEtlLog = models.EtlLog(
            redcap_project = oConnection.unique_name,
            start_date = datetime.datetime.now(),
            status = models.EtlLog.STATUS_ETL_STARTED,
        )
        self.oEtlLog.save()
        self.start_capture_stdout()

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
            options = {'records[0]': pk}
            instrument_names = oConnection.get_instrument_names()
            if instrument_names:
                for idx, instrument_name in enumerate(instrument_names):
                    options['forms[{}]'.format(idx)] = instrument_name
            response = self.run_request('record', oConnection, options)
            if oConnection.projectmetadata.is_longitudinal:
                for entry in response:
                    self.insert_longitudinal(entry, oConnection)
            else:
                for entry in response:
                    self.insert_non_longitudinal(entry, oConnection)
        oConnection.projectmetadata.date_last_downloaded_data = datetime.datetime.now()
        oConnection.projectmetadata.save()

        instruments_loaded = oConnection.get_instrument_names()
        if instruments_loaded:
            instruments_loaded = "\n".join(instruments_loaded)
        self.finish_capture_stdout()
        self.oEtlLog.end_date = datetime.datetime.now()
        self.oEtlLog.query_count = self.query_count
        self.oEtlLog.instruments_loaded = instruments_loaded
        self.comment = "\n".join(self.log_comments)
        self.oEtlLog.save()
        
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
            instrument_name = entry['redcap_repeat_instrument']
            if not oConnection.check_include_instrument( instrument_name ):
                return
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=instrument_name
            )
            oInstrumentMetadata.create_instrument_record(entry, oRoot=oRoot)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.projectmetadata.instrumentmetadata_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                if not oConnection.check_include_instrument(oInstrument.unique_name):
                    continue
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
            instrument_name = entry['redcap_repeat_instrument']
            if not oConnection.check_include_instrument(instrument_name):
                return
            oInstrumentMetadata = models.InstrumentMetadata.objects.get(
                project=oConnection.projectmetadata, unique_name=instrument_name
            )
            oInstrumentMetadata.create_instrument_record(entry, oEvent=oEvent)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            qInstrument = oConnection.projectmetadata.instrumentmetadata_set.exclude(repeatable=True)
            for oInstrument in qInstrument:
                if not oConnection.check_include_instrument(oInstrument.unique_name):
                    continue
                oInstrument.create_instrument_record(entry, oEvent=oEvent)
            

        
        
        
    
        
        
        
        
        
        
        
        
        
        
        