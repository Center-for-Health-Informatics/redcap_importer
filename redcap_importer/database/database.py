from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, ForeignKey, Identity
from sqlalchemy import Integer, String, Date, Text, Float, Boolean, BigInteger

from redcap_importer import redcap_importer_settings as ri_settings
from redcap_importer import models


def map_field_type(django_type):
    """Converts a Django field type to a SQL Alchemy field type"""
    type_map = {
        "TextField": Text,
        "IntegerField": Integer,
        "FloatField": Float,
        "DateField": Date,
        "BooleanField": Boolean,
    }
    return type_map[django_type]


class RedcapDatabase:
    def __init__(self, project_name, metadata_obj=None, use_staging=False):
        self.project = models.RedcapConnection.objects.get(unique_name=project_name)
        self.use_staging = use_staging
        self.is_longitudinal = self.project.projectmetadata.is_longitudinal
        if metadata_obj:
            self.metadata_obj = metadata_obj
        else:
            self.metadata_obj = MetaData()

    def get_schema_name(self):
        """ """
        schema_name = self.project.unique_name
        return schema_name

    def get_sql_alchemy_db_engine(self):
        """Get the SQL Alchemy db engine for the specified dataset.

        :param obj oDataset: Django model object
        :return: SLQ alchemy engine
        """
        schema_name = self.get_schema_name()
        engine = create_engine(
            ri_settings.REDCAP_SQL_ALCHEMY_CONNECTION_STRING,
            connect_args={"options": "-csearch_path={}".format(schema_name)},
        )
        return engine

    def generate_sql_alchemy_table_project_root(self):
        # TODO: I don't think we always use name "study_id"
        project_root_table = Table(
            "project_root",
            self.metadata_obj,
            Column("study_id", String(255), primary_key=True, index=True),
            Column("study_id_display", Text(), nullable=True, index=True),
        )
        return project_root_table

    def generate_sql_alchemy_table_redcap_event(self):
        # only for longitudinal
        if not self.is_longitudinal:
            return None
        pass

    def generate_sql_alchemy_table_instrument(self, oInstrumentMetadata, include_lookups=False):
        table_name = oInstrumentMetadata.get_django_model_name()
        instrument_table = Table(
            table_name,
            self.metadata_obj,
            Column("id", BigInteger, primary_key=True),
            Column("project_root_id", ForeignKey("project_root.study_id"), nullable=False),
            Column("redcap_repeat_instance", Integer),
        )
        # add all columns
        for oField in oInstrumentMetadata.fieldmetadata_set.exclude(is_many_to_many=True):
            column = Column(
                oField.get_django_field_name(),
                map_field_type(oField.django_data_type),
                # index=True,       # I'm getting an error if value is too large to index
            )
            instrument_table.append_column(column)
        if not include_lookups:
            return instrument_table
        field_tables = {}
        for oField in oInstrumentMetadata.fieldmetadata_set.filter(is_many_to_many=True):
            field_table = self.generate_sql_alchemy_table_field_lookup(oField)
            field_name = oField.get_django_field_name()
            field_tables[field_name] = field_table
        return instrument_table, field_tables

    def generate_sql_alchemy_table_field_lookup(self, oFieldMetadata):
        # this won't always be needed, only multiselect fields
        if not oFieldMetadata.is_many_to_many:
            return None
        instrument_name = oFieldMetadata.instrument.get_django_model_name()
        field_name = oFieldMetadata.get_django_field_name()
        table_name = f"{instrument_name}_{field_name}_lookup"
        field_table = Table(
            table_name,
            self.metadata_obj,
            Column("id", BigInteger, primary_key=True),
            Column(f"{instrument_name}_id", ForeignKey(f"{instrument_name}.id"), nullable=False),
            Column(field_name, Text),
            Column(f"{field_name}_display_value", Text),
        )
        return field_table
