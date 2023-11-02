import json
import datetime
from io import StringIO
import sys

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

import requests

from redcap_importer import models
from redcap_importer.database.db_writer import DbWriter


class Command(BaseCommand):
    help = "Populates tables for schema (Instrument and Event) but not Field definitions"

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
        parser.add_argument("connection_name")

    def run_request(self, content, oConnection, addl_options={}):
        addl_options["content"] = content
        addl_options["token"] = oConnection.get_api_token()
        addl_options["format"] = "json"
        addl_options["returnFormat"] = "json"
        self.query_count += 1
        return requests.post(oConnection.api_url.url, addl_options).json()

    def handle(self, *args, **options):
        connection_name = options["connection_name"]
        oConnection = models.RedcapConnection.objects.get(unique_name=connection_name)
        writer = DbWriter(connection_name, use_staging=False)

        # start logging
        self.print_out(oConnection.projectmetadata, log=True)
        self.query_count = 0
        self.oEtlLog = models.EtlLog(
            redcap_project=oConnection.unique_name,
            start_date=datetime.datetime.now(),
            status=models.EtlLog.STATUS_ETL_STARTED,
        )
        self.oEtlLog.save()
        # self.start_capture_stdout()

        writer.initialize_database()

        # get a list of all primary keys
        response = self.run_request(
            "record",
            oConnection,
            {
                "fields": oConnection.projectmetadata.primary_key_field,
            },
        )
        pk_list = []
        for entry in response:
            pk = entry[oConnection.projectmetadata.primary_key_field]
            if not pk in pk_list:
                pk_list.append(pk)

        # load data for one subject at a time
        for pk in pk_list:
            options = {"records[0]": pk}
            instrument_names = oConnection.get_instrument_names()
            if instrument_names:
                for idx, instrument_name in enumerate(instrument_names):
                    options["forms[{}]".format(idx)] = instrument_name
            response = self.run_request("record", oConnection, options)
            for entry in response:
                writer.load_entry(entry)
            # close out bulk-insert queues after each subject finishes (night not be necessary)
            writer.finalize_data()

        writer.finalize_database()

        # finish out logging
        oConnection.projectmetadata.date_last_downloaded_data = datetime.datetime.now()
        oConnection.projectmetadata.save()
        instruments_loaded = oConnection.get_instrument_names()
        if instruments_loaded:
            instruments_loaded = "\n".join(instruments_loaded)
        # self.finish_capture_stdout()
        self.oEtlLog.end_date = datetime.datetime.now()
        self.oEtlLog.query_count = self.query_count
        self.oEtlLog.instruments_loaded = instruments_loaded
        self.comment = "\n".join(self.log_comments)
        self.oEtlLog.save()
