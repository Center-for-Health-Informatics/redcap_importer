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
        try:
            oConnection.projectmetadata.delete()
        except:
            pass
        
        # create new project for connection       
        response = self.run_request('project', oConnection)
        
        oProject = models.ProjectMetadata(
            connection=oConnection,
            project_title=response['project_title'],
            is_longitudinal = response['is_longitudinal'],
        )
        oProject.save()
        
        # get primary_key_field for project
        response = self.run_request('exportFieldNames', oConnection)
        oProject.primary_key_field = response[0]['export_field_name']
        oProject.save()
        
        # check if project is multi-armed
        if oProject.is_longitudinal:
            response = self.run_request('arm', oConnection)
            if len(response) > 1:
                oProject.has_multiple_arms = True
                oProject.save()
        
        # populate Instrument model
        response = self.run_request('instrument', oConnection)
        for entry in response:
            oInstrument = models.InstrumentMetadata(
                project = oProject,
                unique_name = entry['instrument_name'],
                label = entry['instrument_label']
            )
            oInstrument.save()
            
        # populate Arm model
        if oProject.is_longitudinal:
            response = self.run_request('arm', oConnection)
            for entry in response:
                oArm = models.ArmMetadata(
                    arm_number = entry['arm_num'],
                    arm_name = entry['name'],
                    project = oProject,
                )
                oArm.save()
            
        # populate Event model
        if oProject.is_longitudinal:
            response = self.run_request('event', oConnection)
            for i, entry in enumerate(response):
                oArm = models.ArmMetadata.objects.get(
                    project = oProject,
                    arm_number = int( entry['arm_num'] )
                )
                oEvent = models.EventMetadata(
                    project = oProject,
                    unique_name = entry['unique_event_name'],
                    label = entry['event_name'],
                    arm = oArm,
                    ordering = i+1,     # do base 1 counting
                )
                oEvent.save()
        
        # populate EventInstrument model
        
        if oProject.is_longitudinal:
            response = self.run_request('formEventMapping', oConnection)
            ordering = {}               # data structure to help us order instruments for each event starting from 1
            for entry in response:
                oEvent = models.EventMetadata.objects.get(project=oProject, unique_name=entry['unique_event_name'])
                oInstrument = models.InstrumentMetadata.objects.get(project=oProject, unique_name=entry['form'])
                if oEvent.id in ordering:
                    ordering[oEvent.id] += 1
                else:
                    ordering[oEvent.id] = 1
                oEI = models.EventInstrumentMetadata(event=oEvent, instrument=oInstrument)
                oEI.ordering = ordering[oEvent.id]
                oEI.save()
            
        # set repeat instruments and events
        response = self.run_request('repeatingFormsEvents', oConnection)

        print(response)
        if 'error' in response:
            print('repeatingFormsEvents error message: ', response['error'])
            print('No events or instruments will be set to repeating')
        else:
            if oProject.is_longitudinal:
                for entry in response:
                    print('entry', entry)
                    oEvent = models.EventMetadata.objects.get(project=oProject, unique_name=entry['event_name'])
                    if not entry['form_name']:
                        continue            # not sure what causes form for event to be missing, 
                                            # maybe I don't have permission or maybe event isn't setup
                    oInstrument = models.InstrumentMetadata.objects.get(project=oProject, unique_name=entry['form_name'])
                    try:
                        oEI = models.EventInstrumentMetadata.objects.get(event=oEvent, instrument=oInstrument)
                        oEI.repeatable = True
                        oEI.save()
                    except:
                        message = 'Warning: Intrument "{}" is listed as repeating on Event "{}", but the instrument isn\'t associated with that event. Ignoring.'.format(
                            entry['form_name'], entry['event_name'], 
                        ) 
                        print(message)
            else:
                for entry in response:
                    oInstrument = models.InstrumentMetadata.objects.get(unique_name=entry['form_name'])
                    oInstrument.repeatable = True
                    oInstrument.save()
            
        
        # fields
        response = self.run_request('metadata', oConnection)
        ordering = {}               # data structure to help us order fields for each instrument starting from 1
        for entry in response:
            oInstrument = models.InstrumentMetadata.objects.get(project=oProject, unique_name=entry['form_name'])
            django_data_type, field_display_lookup = self.process_field_entry(entry)
            if django_data_type:
                if oInstrument.id in ordering:
                    ordering[oInstrument.id] += 1
                else:
                    ordering[oInstrument.id] = 1
                oField = models.FieldMetadata(
                    instrument = oInstrument,
                    unique_name = entry['field_name'],
                    label = entry['field_label'],
                    ordering = ordering[oInstrument.id],
                    django_data_type = django_data_type,
                    field_display_lookup = json.dumps(field_display_lookup)
                )
                if entry['field_type'] == 'checkbox':
                    oField.is_many_to_many = True
                oField.save()
            
    
            
        
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        