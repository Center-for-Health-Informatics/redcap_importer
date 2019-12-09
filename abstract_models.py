
from django.db import models
from .models import RedcapConnection

from . import helpers


class AbstractProjectRoot(models.Model):

    
    class Meta:
        abstract = True
        ordering = ['pk']
        
    def __str__(self):
        oConn = self._get_connection()
        return '{} = {}'.format(oConn.primary_key_field, self.get_id())
        
    def _get_connection(self):
        if hasattr(self, 'oConnection'):
            return self.oConnection
        app_name = self._meta.app_label
        oConn = RedcapConnection.objects.get(django_app_name=app_name)
        self.oConnection = oConn
        return oConn
    
    def get_id(self):
        oConn = self._get_connection()
        field_name = oConn.primary_key_field
        return getattr(self, field_name)
    
    def get_label(self):
        oConn = self._get_connection()
        field_name = oConn.primary_key_field + '_display'
        return getattr(self, field_name)
    
    def is_longitudinal(self):
        oConn = self._get_connection()
        return oConn.redcapproject.is_longitudinal
    
    def get_instrument_records(self):
        if self.is_longitudinal():
            raise TypeError('Cannot get instruments on the ProjectRoot in a longitudinal study.')
        oConn = self._get_connection()
        instrument_records = []
        for oInstrumentMetadata in oConn.redcapproject.instrument_set.all():
            Instrument = oInstrumentMetadata.get_actual_instrument_model()
            qInstrument = Instrument.objects.filter(project_root=self)
            instrument_records.append({
                'id' : oInstrumentMetadata.unique_name,
                'label' : oInstrumentMetadata.label,
                'table' : helpers.render_instrument_queryset_as_table(qInstrument)
            })
        return instrument_records
    
    def get_event_count(self):
        if not self.is_longitudinal():
            return None
        return self.redcapevent_set.all().count()
    
    def get_instrument_count(self):
        count = 0
        oConn = self._get_connection()
        if self.is_longitudinal():
            for oEvent in self.redcapevent_set.all():
                for oInstrumentMetadata in oConn.redcapproject.instrument_set.all():
                    Instrument = oInstrumentMetadata.get_actual_instrument_model()
                    count += Instrument.objects.filter(redcap_event=oEvent).count()
        else:
            for oInstrumentMetadata in oConn.redcapproject.instrument_set.all():
                Instrument = oInstrumentMetadata.get_actual_instrument_model()
                count += Instrument.objects.filter(project_root=self).count()
        return count
        
    
#     def get_events(self):
#         if not self.is_longitudinal():
#             raise TypeError('Cannot get events on a study that is not longitudinal.')
        
    
class AbstractRedcapEvent(models.Model):
    
    class Meta:
        abstract = True
        ordering = ['event_unique_name']
    
    def __str__(self):
        return self.event_unique_name
    
    def _get_connection(self):
        if hasattr(self, 'oConnection'):
            return self.oConnection
        app_name = self._meta.app_label
        oConn = RedcapConnection.objects.get(django_app_name=app_name)
        self.oConnection = oConn
        return oConn
    
    def get_instrument_records(self):
        oConn = self._get_connection()
        instrument_records = []
        for oInstrumentMetadata in oConn.redcapproject.instrument_set.all():
            Instrument = oInstrumentMetadata.get_actual_instrument_model()
            qInstrument = Instrument.objects.filter(redcap_event=self)
            instrument_records.append({
                'id' : oInstrumentMetadata.unique_name,
                'label' : oInstrumentMetadata.label,
                'table' : helpers.render_instrument_queryset_as_table(qInstrument)
            })
        return instrument_records
    
    
    
    

        
        
        
    
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
            
            
        