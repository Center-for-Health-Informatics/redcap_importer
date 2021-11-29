import json

from django.core.management.base import BaseCommand, CommandError

import requests

from redcap_importer import models
# from redcap_importer import helpers


class Command(BaseCommand):
    help = 'Populates tables for schema (Instrument and Event) but not Field definitions'

#     def add_arguments(self, parser):
#         parser.add_argument('connection_name')

    
        

    def handle(self, *args, **options):
        
        qConnection = models.RedcapConnection.objects.all()
        for oConnection in qConnection:
            print(oConnection.unique_name)
                