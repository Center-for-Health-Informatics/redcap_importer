from django.contrib import admin
from . import models


class RedcapApiUrlAdmin(admin.ModelAdmin):
    list_display = ("name", "url")


admin.site.register(models.RedcapApiUrl, RedcapApiUrlAdmin)


class IncludeInstrumentAdmin(admin.TabularInline):  # can also use StackedInline
    model = models.IncludeInstrument
    extra = 3


class RedcapConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "unique_name",
        "partial_load",
    )
    inlines = [IncludeInstrumentAdmin]


admin.site.register(models.RedcapConnection, RedcapConnectionAdmin)


class ProjectMetadataAdmin(admin.ModelAdmin):
    list_display = (
        "project_title",
        "primary_key_field",
        "connection",
        "is_longitudinal",
        "has_multiple_arms",
    )


admin.site.register(models.ProjectMetadata, ProjectMetadataAdmin)


class EventMetadataAdmin(admin.ModelAdmin):
    list_display = ("unique_name", "project", "label", "ordering", "repeatable")
    list_filter = ("project",)


admin.site.register(models.EventMetadata, EventMetadataAdmin)

# @admin.action not available before django 3.2
# @admin.action(description='Include instruments during data load')
def include_instruments(modeladmin, request, queryset):
    for oInstrument in queryset:
        oInclude, created = models.IncludeInstrument.objects.get_or_create(
            connection=oInstrument.project.connection,
            instrument_name=oInstrument.unique_name,
        )


include_instruments.short_description = "Include instruments during data load"


class InstrumentMetadataAdmin(admin.ModelAdmin):
    list_display = (
        "unique_name",
        "project",
        "label",
        "unique_name",
        "repeatable",
        "instrument_will_load",
    )
    list_filter = ("project",)
    actions = [include_instruments]


admin.site.register(models.InstrumentMetadata, InstrumentMetadataAdmin)


class EventInstrumentMetadataAdmin(admin.ModelAdmin):
    list_display = ("event", "instrument", "repeatable")


admin.site.register(models.EventInstrumentMetadata, EventInstrumentMetadataAdmin)


class FieldMetadataAdmin(admin.ModelAdmin):
    list_display = (
        "unique_name",
        "instrument",
        "django_data_type",
        "label",
        "ordering",
        "is_many_to_many",
        "field_display_lookup",
    )
    list_filter = ("instrument__project", "instrument")


admin.site.register(models.FieldMetadata, FieldMetadataAdmin)


class EtlLogAdmin(admin.ModelAdmin):
    list_display = (
        "redcap_project",
        "direction",
        "status",
        "start_date",
        "end_date",
        "get_duration",
        "query_count",
        "last_successful_record_number",
        "get_loaded_count",
    )
    list_filter = ("direction", "status")


admin.site.register(models.EtlLog, EtlLogAdmin)
