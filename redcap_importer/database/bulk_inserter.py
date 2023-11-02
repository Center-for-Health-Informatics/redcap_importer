import json
from sqlalchemy import MetaData, text, select, insert

from redcap_importer import models
from redcap_importer.database.database import RedcapDatabase


class BulkInserter:
    def __init__(self, project_name, use_staging=False):
        self.connection = models.RedcapConnection.objects.get(unique_name=project_name)
        self.use_staging = use_staging
        self.project_root_records = []
        self.redcap_event_records = []
        self.instrument_records = {}
        self.lookup_table_records = {}
        self.index_tracker = 1
        self.metadata_obj = MetaData()
        self.database = RedcapDatabase(project_name, self.metadata_obj, self.use_staging)
        self.engine = self.database.get_sql_alchemy_db_engine()
        self.generate_table_objects()

    def generate_table_objects(self):
        """Generate all sql alchemy table objects once and reuse as needed"""
        self.project_root_table = self.database.generate_sql_alchemy_table_project_root()
        self.instrument_tables = {}
        self.lookup_tables = {}
        for oInstrument in self.connection.get_all_instruments():
            inst_table, lookup_tables = self.database.generate_sql_alchemy_table_instrument(
                oInstrument, include_lookups=True
            )
            self.instrument_tables[oInstrument.get_django_model_name()] = inst_table
            for lookup_table_name, lookup_table in lookup_tables.items():
                self.lookup_tables[lookup_table_name] = lookup_table

    def queue_project_root(self, record):
        self.project_root_records.append(record)

    def queue_redcap_event(self, record):
        pass

    def get_instrument_id(self, instrument_table_name):
        """
        Get an id value to add to the record. This is used to get an ID for a record that might
        not get added to the queue.
        """
        next_id = self.index_tracker
        self.index_tracker += 1
        return next_id

    def queue_instrument(self, instrument_table_name, record):
        if not "id" in record:
            record["id"] = self.index_tracker
            self.index_tracker += 1
        if not instrument_table_name in self.instrument_records:
            self.instrument_records[instrument_table_name] = []
        self.instrument_records[instrument_table_name].append(record)

    def queue_lookup_table(self, lookup_table_name, record):
        record["id"] = self.index_tracker
        self.index_tracker += 1
        if not lookup_table_name in self.lookup_table_records:
            self.lookup_table_records[lookup_table_name] = []
        self.lookup_table_records[lookup_table_name].append(record)

    def clear_all_queues(self):
        # clear in order project_root, redcap_events, instruments, lookups
        # print("===project records =================")
        # print(json.dumps(self.project_root_records, indent=4, default=str))
        # print("===instrument_records =================")
        # print(json.dumps(self.instrument_records, indent=4, default=str))
        # print("===lookup_table_records =================")
        # print(json.dumps(self.lookup_table_records, indent=4, default=str))
        with self.engine.begin() as conn:
            result = conn.execute(insert(self.project_root_table), self.project_root_records)
            # print("a", result)
            self.project_root_records = []
            for inst_name, inst_records in self.instrument_records.items():
                inst_table = self.instrument_tables[inst_name]
                # print(inst_table, json.dumps(self.instrument_records, indent=4, default=str))
                result = conn.execute(insert(inst_table), inst_records)
                # print("b", inst_table, result)
            self.instrument_records = {}
            for lookup_table_name, lookup_table_records in self.lookup_table_records.items():
                lookup_table = self.lookup_tables[lookup_table_name]
                result = conn.execute(insert(lookup_table), lookup_table_records)
                # print("b", lookup_table, result)
            self.lookup_table_records = {}
