from django.contrib import admin
from . import models



class RedcapApiUrlAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    
admin.site.register(models.RedcapApiUrl, RedcapApiUrlAdmin)

class RedcapConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'unique_name',)
    
admin.site.register(models.RedcapConnection, RedcapConnectionAdmin)


class ProjectMetadataAdmin(admin.ModelAdmin):
    list_display = ('project_title', 'primary_key_field', 'connection', 'is_longitudinal', 'has_multiple_arms')
    
admin.site.register(models.ProjectMetadata, ProjectMetadataAdmin)


class EventMetadataAdmin(admin.ModelAdmin):
    list_display = ('unique_name', 'project', 'label', 'ordering', 'repeatable')
    list_filter = ('project', )
    
admin.site.register(models.EventMetadata, EventMetadataAdmin)


class InstrumentMetadataAdmin(admin.ModelAdmin):
    list_display = ('unique_name', 'project', 'label', 'unique_name', 'repeatable')
    list_filter = ('project', )
    
admin.site.register(models.InstrumentMetadata, InstrumentMetadataAdmin)


class EventInstrumentMetadataAdmin(admin.ModelAdmin):
    list_display = ('event', 'instrument', 'repeatable')
    
admin.site.register(models.EventInstrumentMetadata, EventInstrumentMetadataAdmin)


class FieldMetadataAdmin(admin.ModelAdmin):
    list_display = ('unique_name', 'instrument', 'django_data_type', 'label', 'ordering', 'is_many_to_many', 'field_display_lookup')
    list_filter = ('instrument__project', 'instrument')
    
admin.site.register(models.FieldMetadata, FieldMetadataAdmin)