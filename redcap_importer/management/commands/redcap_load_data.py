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
        self.print_out(oConnection.projectmetadata, log=True)
        self.query_count = 0

        writer.initialize_database()
