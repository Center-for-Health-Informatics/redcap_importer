import json

from django.core.management.base import BaseCommand, CommandError

import requests

from redcap_importer import models
# from redcap_importer import helpers


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
        
        # get connection and delete existing project
        oConnection = models.RedcapConnection.objects.get(unique_name=connection_name)
        oProject = oConnection.projectmetadata
        
        output = []
        has_major_project_change = False

        # check basic project setup for changes
        project_response = self.run_request('project', oConnection)
        if project_response['is_longitudinal'] != oProject.is_longitudinal:
            has_major_project_change = True
            output.append("Longitudinality of this project has changed from {} to {}".format(
                oProject.is_longitudinal, project_response['is_longitudinal']
            ))
        
        # check primary_key_field for project
        field_name_response = self.run_request('exportFieldNames', oConnection)
        if field_name_response[0]['export_field_name'] != oProject.primary_key_field:
            has_major_project_change = True
            output.append("The project primary key field has changed from {} to {}".format(
                oProject.primary_key_field, field_name_response[0]['export_field_name']
            ))
        
        # check if project is multi-armed
        if project_response['is_longitudinal']:
            response = self.run_request('arm', oConnection)
            if len(response) > 1 and not oProject.has_multiple_arms:
                has_major_project_change = True
                output.append("The project has been changed from single armed to multi armed")
            elif len(response) <= 1 and oProject.has_multiple_arms:
                has_major_project_change = True
                output.append("The project has been changed from multi armed to single armed")
                
        if has_major_project_change:
            for comment in output:
                print(comment)
            return
        
        # check for new instruments
        response = self.run_request('instrument', oConnection)
        loaded_instruments = []
        for entry in response:
            loaded_instruments.append(entry['instrument_name'])
            oInstrument = models.InstrumentMetadata.objects.filter(
                project = oProject,
                unique_name = entry['instrument_name']
            ).first()
            if not oInstrument:
                output.append("New instrument: {}".format(entry['instrument_name']))
                
        # check for missing instruments
        for oInstrument in models.InstrumentMetadata.objects.filter(project=oProject):
            if not oInstrument.unique_name in loaded_instruments:
                output.append("Instrument removed: {}".format(oInstrument.unique_name))
            
#         # populate Arm model
#         if oProject.is_longitudinal:
#             response = self.run_request('arm', oConnection)
#             for entry in response:
#                 oArm = models.ArmMetadata(
#                     arm_number = entry['arm_num'],
#                     arm_name = entry['name'],
#                     project = oProject,
#                 )
#                 oArm.save()
            
        # check for new events
        if oProject.is_longitudinal:
            response = self.run_request('event', oConnection)
            loaded_events = []
            for entry in response:
                loaded_events.append(entry['unique_event_name'])
                oArm = models.ArmMetadata.objects.get(
                    project = oProject,
                    arm_number = int( entry['arm_num'] )
                )
                oEvent = models.EventMetadata.objects.filter(
                    project = oProject,
                    unique_name = entry['unique_event_name'],
                    arm = oArm,
                ).first()
                if not oEvent:
                    output.append("New event: {}".format(entry['unique_event_name']))
                    
        # check for missing events
        for oEvent in models.EventMetadata.objects.filter(project=oProject):
            if not oEvent.unique_name in loaded_events:
                output.append("Event removed: {}".format(oEvent.unique_name))

        
#         # populate EventInstrument model
#          
#         if oProject.is_longitudinal:
#             response = self.run_request('formEventMapping', oConnection)
#             ordering = {}               # data structure to help us order instruments for each event starting from 1
#             for entry in response:
#                 oEvent = models.EventMetadata.objects.get(project=oProject, unique_name=entry['unique_event_name'])
#                 oInstrument = models.InstrumentMetadata.objects.get(project=oProject, unique_name=entry['form'])
#                 if oEvent.id in ordering:
#                     ordering[oEvent.id] += 1
#                 else:
#                     ordering[oEvent.id] = 1
#                 oEI = models.EventInstrumentMetadata(event=oEvent, instrument=oInstrument)
#                 oEI.ordering = ordering[oEvent.id]
#                 oEI.save()
#             
#         # set repeat instruments and events
#         response = self.run_request('repeatingFormsEvents', oConnection)
# 
#         print(response)
#         if 'error' in response:
#             print('repeatingFormsEvents error message: ', response['error'])
#             print('No events or instruments will be set to repeating')
#         else:
#             if oProject.is_longitudinal:
#                 for entry in response:
#                     print('entry', entry)
#                     oEvent = models.EventMetadata.objects.get(project=oProject, unique_name=entry['event_name'])
#                     if not entry['form_name']:
#                         continue            # not sure what causes form for event to be missing, 
#                                             # maybe I don't have permission or maybe event isn't setup
#                     oInstrument = models.InstrumentMetadata.objects.get(project=oProject, unique_name=entry['form_name'])
#                     try:
#                         oEI = models.EventInstrumentMetadata.objects.get(event=oEvent, instrument=oInstrument)
#                         oEI.repeatable = True
#                         oEI.save()
#                     except:
#                         message = 'Warning: Intrument "{}" is listed as repeating on Event "{}", but the instrument isn\'t associated with that event. Ignoring.'.format(
#                             entry['form_name'], entry['event_name'], 
#                         ) 
#                         print(message)
#             else:
#                 for entry in response:
#                     oInstrument = models.InstrumentMetadata.objects.get(unique_name=entry['form_name'])
#                     oInstrument.repeatable = True
#                     oInstrument.save()
            
        
        # fields
        response = self.run_request('metadata', oConnection)
        loaded_fields = []
        for entry in response:
            oInstrument = models.InstrumentMetadata.objects.filter(project=oProject, unique_name=entry['form_name']).first()
            if not oInstrument:
                # this is a new instrument, info about it should already be in the report
                continue
            django_data_type, field_display_lookup = self.process_field_entry(entry)
            if django_data_type:
                loaded_fields.append(entry['field_name'])
                oField = models.FieldMetadata.objects.filter(
                    instrument = oInstrument,
                    unique_name = entry['field_name'],
                    django_data_type = django_data_type
                ).first()
                if not oField:
                    output.append("New field: {}.{}".format(oInstrument.unique_name, entry['field_name']))
                    
        # check for missing fields
        for oInstrument in models.InstrumentMetadata.objects.filter(project=oProject):
            if oInstrument.unique_name in loaded_instruments:
                for oField in models.FieldMetadata.objects.filter(instrument=oInstrument):
                    if not oField.unique_name in loaded_fields:
                        output.append("Field removed: {}.{}".format(oInstrument.unique_name, oField.unique_name))
            
        
        for comment in output:
            print(comment)
        return
    
            
        
    def process_field_entry(self, entry):
        field_type = entry['field_type']
        if field_type in ['yesno', 'truefalse']:
            return ( 'BooleanField', {} )
        if field_type in ['descriptive', 'notes', 'sql', 'slider', ]:
            return ( 'TextField', {} )
        if field_type == 'calc':
            return ('FloatField', {})
        if field_type == 'text':
            return self._process_text_field_entry(entry)
        if field_type in ['dropdown', 'checkbox', 'radio']:
            return self._process_select_field_entry(entry)
        if field_type in ['file']:             # not sure how these work
            return (None, None)
        print(entry)
        raise ValueError('Field type not recognized: {}'.format(field_type))
    
    def _process_select_field_entry(self, entry):
        options = entry['select_choices_or_calculations'].split('|')
        lookup_data = {}
        for option in options:
            option_id = option.split(',', 1)[0].strip().lower()
            option_value = option.split(',', 1)[1].strip()
            lookup_data[option_id] = option_value
        return ('TextField', lookup_data)
        
    def _process_text_field_entry(self, entry):
        redcap_data_type = entry['text_validation_type_or_show_slider_number']
        if redcap_data_type == 'number':
            return ('FloatField', {})
        if redcap_data_type == 'integer':
            return ('IntegerField', {})
        if redcap_data_type == 'date_mdy':
            return ('DateField', {})
        return ('TextField', {})
        
        
        
        
        
        
        
        
        
        
        
        
        
        