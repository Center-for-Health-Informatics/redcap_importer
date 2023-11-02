from sqlalchemy import MetaData, text, select

from redcap_importer.database.database import RedcapDatabase
from redcap_importer import models
from redcap_importer.database.bulk_inserter import BulkInserter


class DbWriter:
    """
    Handles actual data schema in the database.
    Translates REDCap API responses into database records (saved as dicts) that then get passed
    to the bulk inserter.
    """

    def __init__(self, project_name, use_staging=False):
        self.connection = models.RedcapConnection.objects.get(unique_name=project_name)
        self.use_staging = use_staging
        self.is_longitudinal = self.connection.projectmetadata.is_longitudinal
        self.metadata_obj = MetaData()
        self.database = RedcapDatabase(project_name, self.metadata_obj, self.use_staging)
        self.engine = self.database.get_sql_alchemy_db_engine()
        self.instruments = self.connection.get_all_instruments()
        self.bulk_inserter = BulkInserter(project_name, use_staging)
        self.finished_project_root_ids = []

    def initialize_database(self):
        # (re)create the schema
        schema_name = self.database.get_schema_name()
        with self.engine.connect() as conn:
            print("starting schema reset")
            sql = f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"
            conn.execute(text(sql))
            conn.commit()
            sql = f"CREATE SCHEMA {schema_name}"
            conn.execute(text(sql))
            conn.commit()
            print("ending schema reset")
        # create the tables
        self.database.generate_sql_alchemy_table_project_root()
        if self.is_longitudinal:
            self.database.generate_sql_alchemy_table_redcap_event()
        for oInstrument in self.instruments:
            self.database.generate_sql_alchemy_table_instrument(oInstrument, include_lookups=True)
        self.metadata_obj.create_all(self.engine)

    def load_entry(self, entry):
        """
        Takes a single record from the REDCap API and generates any database records needed,
        then queues them into the bulk inserter.
        """
        if self.is_longitudinal:
            self._load_longitudinal_entry(entry)
        else:
            self._load_non_longitudinal_entry(entry)

    def _load_longitudinal_entry(self, entry):
        pass

    def _load_non_longitudinal_entry(self, entry):
        # create project root if needed
        pk_field = self.connection.projectmetadata.primary_key_field
        project_root_id = entry[pk_field]
        if project_root_id not in self.finished_project_root_ids:
            project_record = {"study_id": project_root_id}
            self.bulk_inserter.queue_project_root(project_record)
            self.finished_project_root_ids.append(project_root_id)
        if "redcap_repeat_instrument" in entry and entry["redcap_repeat_instrument"]:
            # figure out one instrument record and create
            self._load_one_repeating_instrument(project_root_id, entry)
        else:
            # base_record, load all non-repeating instruments (verify not empty)
            self._load_all_non_repeating_instruments(project_root_id, entry)

    def _load_one_repeating_instrument(self, project_root_id, entry):
        """
        In non-longituindal, repeating instruments records will each get their own dedicated
        entry. this loads one repeating instrument.
        """
        instrument_name = entry["redcap_repeat_instrument"]
        if not self.connection.check_include_instrument(instrument_name):
            return
        oInstrumentMetadata = models.InstrumentMetadata.objects.get(
            project=self.connection.projectmetadata, unique_name=instrument_name
        )
        instrument_record_base = {
            "project_root_id": project_root_id,
            "redcap_repeat_instance": entry["redcap_repeat_instance"],
        }
        self._create_instrument_record(oInstrumentMetadata, instrument_record_base, entry)

    def _create_instrument_record(self, oInstrument, inst_record_base, entry):
        # skip if there is no data to load for the instrument
        inst_has_data = False
        for oField in oInstrument.fieldmetadata_set.all():
            if oField.check_value_exists(entry):
                inst_has_data = True
        if not inst_has_data:
            return
        instrument_name = oInstrument.get_django_model_name()
        # populate instrument record
        inst_record = inst_record_base
        for oField in oInstrument.fieldmetadata_set.filter(is_many_to_many=False):
            value, field_has_display_values, display_value = oField.get_value_for_standard_field(
                entry
            )
            django_field_name = oField.get_django_field_name()
            inst_record[django_field_name] = value
            if field_has_display_values:
                inst_record[f"{django_field_name}_display_value"] = display_value
        # populate m2m lookup tables
        instrument_id = self.bulk_inserter.get_instrument_id(instrument_name)
        for oField in oInstrument.fieldmetadata_set.filter(is_many_to_many=True):
            values = oField.get_values_for_m2m_field(entry)
            for value, display_value in values:
                field_name = oField.get_django_field_name()
                record = {
                    f"{instrument_name}_id": instrument_id,
                    field_name: value,
                    f"{field_name}_display_value": display_value,
                }
                self.bulk_inserter.queue_lookup_table(field_name, record)
        # save instrument record
        inst_record["id"] = instrument_id
        self.bulk_inserter.queue_instrument(instrument_name, inst_record)

    def _load_all_non_repeating_instruments(self, project_root_id, entry):
        """
        In non-longituindal, non repeating instruments for a subject will be grouped into one
        entry. this loads all of them, and will ignore any instruments that have no data.
        """
        qInstrument = self.connection.projectmetadata.instrumentmetadata_set.exclude(
            repeatable=True
        )
        for instrument in qInstrument:
            instrument_record_base = {
                "project_root_id": project_root_id,
                "redcap_repeat_instance": None,
            }
            self._create_instrument_record(instrument, instrument_record_base, entry)

    def finalize_data(self):
        """
        Closes out any bulk insert queues that are not finished
        """
        self.bulk_inserter.clear_all_queues()

    def finalize_database(self):
        """
        If using a staging schema, this will replace the prod schema with the staging schema
        """
        # make sure no data left in queues
        # self.bulk_inserter.clear_all_queues()
        pass
