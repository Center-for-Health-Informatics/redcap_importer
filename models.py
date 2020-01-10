import json
import collections
import datetime
from dateutil.parser import parse

from django.db import models
from django.apps import apps

from pymongo import MongoClient
from django.conf import settings




class RedcapApiUrl(models.Model):
    name                        = models.CharField(max_length=255, unique=True)
    url                         = models.URLField(unique=True)
    
    def __str__(self):
        return '{} ({})'.format(self.name, self.url)
    

class RedcapConnection(models.Model):
    name                        = models.CharField(max_length=255, unique=True)
    unique_name                 = models.SlugField(unique=True,
                                        help_text='This will be the name of the Django app or Mongo collection')
    api_url                     = models.ForeignKey('RedcapApiUrl', on_delete=models.PROTECT)
    api_token                   = models.CharField(max_length=255)
#     primary_key_field           = models.CharField(max_length=255,
#                                         help_text='ex. record_id, study_id, etc.')
    
    def __str__(self):
        return self.name
    
    def has_project(self):
        return hasattr(self, 'projectmetadata')
    


class ProjectMetadata(models.Model):
    connection                  = models.OneToOneField('RedcapConnection', on_delete=models.CASCADE)
    project_title               = models.CharField(max_length=255)
    is_longitudinal             = models.BooleanField()
    has_multiple_arms           = models.BooleanField(default=False)
    date_last_updated_metadata  = models.DateTimeField(auto_now_add=True)
    date_last_downloaded_data   = models.DateTimeField(blank=True, null=True)
    date_last_downloaded_data_mongo = models.DateTimeField(blank=True, null=True)
    date_last_uploaded_data     = models.DateTimeField(blank=True, null=True)
    primary_key_field           = models.CharField(max_length=255,
                                        help_text='ex. record_id, study_id, etc.')
    
    def __str__(self):
        return 'PROJECT: {}'.format(self.project_title)
    
    def get_actual_project_root_model(self):
        app_name = self.connection.unique_name
        model_name = 'ProjectRoot'
        try:
            RootModel = apps.get_model(app_label=app_name, model_name=model_name)
        except:
            return None
        return RootModel
    
    def get_mongo_collection(self):
        con = settings.REDCAP_IMPORTER_MONGO_CONNECTION_SETTINGS
        mongo_client = MongoClient(**con)
        mongo_db = mongo_client[self.connection.unique_name]
        return mongo_db.root
    
    def get_project_queryset_or_collection(self, data_source):
        if data_source == 'mongo':
            return self.get_mongo_collection()
        ProjectRoot = self.get_actual_project_root_model()
        return ProjectRoot.objects.all()
    
    def get_count(self):
        MyModel = self.get_actual_project_root_model()
        if MyModel:
            return MyModel.objects.all().count()
        return 0
    
    def get_count_mongo(self):
        collection = self.get_mongo_collection()
        return collection.find().count()
    
    def count_arms(self):
        arms = self.get_events_grouped_by_arm()
        return len(arms)
    
    def get_events_grouped_by_arm(self):
        arms = {}
        for oEvent in self.eventmetadata_set.all():
            arm_number = oEvent.unique_name.split('_')[-1]
            if not arm_number in arms:
                arms[arm_number] = []
            arms[arm_number].append(oEvent)
        return arms
        
    
    def count_arms(self):
        arms = self.get_events_grouped_by_arm()
        return len(arms)
    
    def get_events_grouped_by_arm(self):
        arms = {}
        for oEvent in self.eventmetadata_set.all():
            arm_number = oEvent.unique_name.split('_')[-1]
            if not arm_number in arms:
                arms[arm_number] = []
            arms[arm_number].append(oEvent)
        return arms
        

class ArmMetadata(models.Model):
    project                     = models.ForeignKey('ProjectMetadata', on_delete=models.CASCADE)
    arm_number                  = models.IntegerField()
    arm_name                    = models.TextField()
    
    class Meta:
        unique_together = (("project", "arm_number"),)
        ordering = ('arm_number', )
            
    
class EventMetadata(models.Model):
    project                     = models.ForeignKey('ProjectMetadata', on_delete=models.CASCADE)
    arm                         = models.ForeignKey('ArmMetadata', on_delete=models.CASCADE)
    unique_name                 = models.CharField(max_length=255, help_text='unique for RedcapProject')
    label                       = models.TextField()
    ordering                    = models.IntegerField()
    repeatable                  = models.BooleanField(default=False)
    
    class Meta:
        unique_together = (("project", "unique_name"),)
        ordering = ('ordering', )
    
    def __str__(self):
        return 'EVENT: {}'.format(self.unique_name)
    
    def get_or_create_event_record(self, oRoot):
        #!! TO DO: consider how repeatable entire events would work
        EventModel = self.get_actual_instrument_model()
        oEvent, created = EventModel.objects.get_or_create(
            project_root=oRoot,
            event_unique_name=self.unique_name,
            event_label=self.label,
            arm_number=self.arm.arm_number
        )
        return oEvent
    
    def get_actual_event_model(self):
        app_name = self.project.connection.unique_name
        model_name = 'RedcapEvent'
        try:
            EventModel = apps.get_model(app_label=app_name, model_name=model_name)
        except:
            return None
        return EventModel
    
    def get_count(self):
        EventModel = self.get_actual_event_model()
        if EventModel:
            return EventModel.objects.filter(event_unique_name=self.unique_name).count()
        return 0
    

    
    
            
    
class EventInstrumentMetadata(models.Model):
    event                       = models.ForeignKey('EventMetadata', on_delete=models.CASCADE)
    instrument                  = models.ForeignKey('InstrumentMetadata', on_delete=models.CASCADE)
    repeatable                  = models.BooleanField(default=False,
                                        help_text='should be false if associated event is repeatable')
    ordering                    = models.IntegerField()
    
    def __str__(self):
        return '{} : {}'.format(self.event, self.instrument)
    
    
class InstrumentMetadata(models.Model):
    project                     = models.ForeignKey('ProjectMetadata', on_delete=models.CASCADE)
    unique_name                 = models.CharField(max_length=255, help_text='unique for RedcapProject')
    django_model_name           = models.CharField(max_length=255, help_text='set if different from unique_name', blank=True, null=True)
    label                       = models.TextField()
    repeatable                  = models.BooleanField(default=False,
                                        help_text='this will be ignored for longitudinal studies, use EventInstrument.repeatable instead')
    
    class Meta:
        unique_together = (("project", "unique_name"),)
    
    def __str__(self):
        return 'INSTRUMENT: {}'.format(self.unique_name)
    
    def get_django_model_name(self):
        return self.django_model_name if self.django_model_name else self.unique_name
    
    def get_actual_instrument_model(self):
        app_name = self.project.connection.unique_name
        model_name = self.get_django_model_name()
        try:
            InstrumentModel = apps.get_model(app_label=app_name, model_name=model_name)
        except:
            return None
        return InstrumentModel
    
    def get_count(self):
        MyModel = self.get_actual_instrument_model()
        if MyModel:
            return MyModel.objects.all().count()
        return 0
    
    def get_count_mongo(self):
         # must be a faster way to do this
        # https://stackoverflow.com/questions/32305897/mongodb-count-all-array-elements-in-all-objects-matching-by-criteria
        collection = self.project.get_mongo_collection()
        count = 0
        for doc in collection.find():
            if 'instruments' in doc and self.unique_name in doc['instruments']:
                count += len( doc['instruments'][self.unique_name] )
        return count
    
    def create_instrument_dict(self, entry):
        response = {}
        data_exists = False
        for oField in self.fieldmetadata_set.all():
            if oField.check_value_exists(entry):
                data_exists = True
        if not data_exists:
            return None
        for oField in self.fieldmetadata_set.all():
            if oField.unique_name in entry:
                value = entry[oField.unique_name]
                if isinstance(value, datetime.date):
                    value = datetime.combine(value, datetime.min.time())
                response[oField.get_django_field_name()] = value
        return response
    
    def create_instrument_record(self, entry, oRoot=None, oEvent=None):
        # EITHER OROOT OR OEVENT SHOULD BE SET, NOT BOTH
        # go ahead and return none if no data
        data_exists = False
        for oField in self.fieldmetadata_set.all():
            if oField.check_value_exists(entry):
                data_exists = True
        if not data_exists:
            return None
        app_name = self.project.connection.unique_name
        ActualInstrument = apps.get_model(app_label=app_name, model_name=self.get_django_model_name())
        oActualInstrument = ActualInstrument()
        if oRoot:
            oActualInstrument.project_root = oRoot
        else:
            oActualInstrument.redcap_event = oEvent
        if 'redcap_repeat_instance' in entry and entry['redcap_repeat_instance'] != '':
            oActualInstrument.redcap_repeat_instance = int(entry['redcap_repeat_instance'])
        # set metadata values like redcap repeat instance
        oActualInstrument.save()
        for oField in self.fieldmetadata_set.all():
            oField.add_value_to_instrument(oActualInstrument, entry)
        oActualInstrument.save()
        return oActualInstrument
        
    
class FieldMetadata(models.Model):
    instrument                  = models.ForeignKey('InstrumentMetadata', on_delete=models.CASCADE)
    django_data_type            = models.CharField(max_length=120, help_text='ex. DateField, TextField')
    unique_name                 = models.CharField(max_length=255, help_text='unique for Instrument')
    django_field_name           = models.CharField(max_length=255, help_text='set if different from unique_name', blank=True, null=True)
    label                       = models.TextField()
    ordering                    = models.IntegerField()
    field_display_lookup        = models.TextField(default='{}',
                                    help_text='If set, creates a second field [field_name]_display and attempts to populate it with lookup val')
    is_many_to_many             = models.BooleanField(default=False)
    
    
    def __str__(self):
        return 'FIELD: {}'.format(self.unique_name)
    
    class Meta:
        ordering = ['ordering']
        
    def get_display_lookup(self):
        lookup = json.loads(self.field_display_lookup)
        return lookup
    
    def get_django_field_name(self):
        return self.django_field_name if self.django_field_name else self.unique_name
    
    def get_field_values(self):
        InstrumentModel = self.instrument.get_actual_instrument_model()
        if self.is_many_to_many:
            app_name = self.instrument.project.connection.unique_name
            model_name='{}_{}_lookup'.format(
                self.instrument.get_django_model_name(), 
                self.get_django_field_name()
            )
            LookupModel = apps.get_model(app_label=app_name, model_name=model_name)
            qField = LookupModel.objects.all().values_list(
                self.get_django_field_name() + '_display_value', flat=True
            )
        
        elif self.get_display_lookup():
            qField = InstrumentModel.objects.all().values_list(
                self.get_django_field_name() + '_display_value', flat=True
            )
        else:
            qField = InstrumentModel.objects.all().values_list(
                self.get_django_field_name(), flat=True
            )
        return list(qField)
    
    def get_field_values_mongo(self):
        response = []
        collection = self.instrument.project.get_mongo_collection()
        for doc in collection.find():
            instrument = self.instrument.unique_name
            field = self.unique_name
            if 'instruments' in doc and instrument in doc['instruments']:
                for record in doc['instruments'][instrument]:
                    if field in record and record[field]:
                        response.append(record[field])
                    else:
                        response.append(None)
        return response


    
    def get_stats(self):
        values = self.get_field_values()
        
        val_temp = list(x for x in values if x is not None)
        val_temp.sort()
        stats = {
            'count' : len(values),
            # 'distinct' : len(set(values)),
            'count_null' : sum(x is None for x in values),
            
        }
        stats['count_not_null'] = stats['count'] - stats['count_null']
        not_none_list =  [i for i in val_temp if not i is None]
        if not_none_list:
            stats['min'] = min(not_none_list)
            stats['max'] = max(not_none_list)
            stats['distinct'] = len(set(not_none_list))
        else:
            stats['distinct'] = 0
            
        stats['count_non_null'] = stats['count'] - stats['count_null']
        all_counts = dict(collections.Counter(values).most_common(10))      # list of all distinct values with counts
        return (stats, all_counts)
        
   
    def _get_many_to_many_redcap_fields(self):
        if not self.is_many_to_many:
            return {}
        names = {}
        for key in self.get_display_lookup():
            names[key] = '{}___{}'.format(self.unique_name, key)
        return names
    
    def get_many_to_many_count(self):
        if not self.is_many_to_many:
            return 0
        app_name = self.instrument.project.connection.unique_name
        model_name='{}_{}_lookup'.format(
            self.instrument.get_django_model_name(), 
            self.get_django_field_name()
        )
        try:
            LookupModel = apps.get_model(app_label=app_name, model_name=model_name)
        except:
            return 0
        return LookupModel.objects.all().count()
            
    
    def check_value_exists(self, entry):
        if self.is_many_to_many:
            for key, field_name in self._get_many_to_many_redcap_fields().items():
                if field_name != '':
                    return True
            return False
        else:
            if not self.unique_name in entry:
                print('field missing from data: {}'.format(self.unique_name))
                return False
            value = entry[self.unique_name]
            return False if value == '' else True
            
        
    def add_value_to_instrument(self, oInstrument, entry):
        if self.is_many_to_many:
            field_names = self._get_many_to_many_redcap_fields()
            for key, field_name in field_names.items():
                if entry[field_name] == '1':
                    app_name = self.instrument.project.connection.unique_name
                    model_name='{}_{}_lookup'.format(
                        self.instrument.get_django_model_name(), 
                        self.get_django_field_name()
                    )
                    LookupModel = apps.get_model(app_label=app_name, model_name=model_name)
                    display_value = self.get_display_lookup()[key]
                    args = {
                        self.instrument.get_django_model_name() : oInstrument,
                        self.get_django_field_name() : key,
                        self.get_django_field_name() + '_display_value' : display_value,
                    }
                    oLookupModel = LookupModel(**args)
                    oLookupModel.save()
        else:
            if not self.unique_name in entry:
                print('field missing from data: {}'.format(self.unique_name))
                return 
            if entry[self.unique_name] == '':
                return
            if self.django_data_type == 'FloatField':
                value = float(entry[self.unique_name])
            elif self.django_data_type == 'IntegerField':
                value = int(entry[self.unique_name])
            elif self.django_data_type == 'DateField':
                date_str = entry[self.unique_name]
                if date_str:
                    try:
                        value = parse(date_str)
                    except ValueError:
                        print('unable to convert string to date: {}'.format(date_str))
                        return
            else:
                value = entry[self.unique_name]
            setattr(oInstrument, self.get_django_field_name(), value)
            lookup = self.get_display_lookup()
            if lookup:
                print('lookup')
                print(self)
                print(oInstrument)
                print(entry)
                print('---')
                setattr(oInstrument, 
                        self.get_django_field_name() + '_display_value', 
                        lookup[value.lower()]
                )
    















