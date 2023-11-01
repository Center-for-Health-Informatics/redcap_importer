from sqlalchemy import MetaData, text, select

from redcap_importer.database.database import RedcapDatabase
from redcap_importer import models


class DbWriter:
    def __init__(self, project_name, use_staging=False):
        self.project = models.RedcapConnection.objects.get(unique_name=project_name)
        self.use_staging = use_staging
        self.is_longitudinal = self.project.projectmetadata.is_longitudinal
        self.metadata_obj = MetaData()
        self.database = RedcapDatabase(project_name, self.metadata_obj, self.use_staging)
        self.engine = self.database.get_sql_alchemy_db_engine()

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
        for oInstrument in self.project.get_all_instruments():
            self.database.generate_sql_alchemy_table_instrument(oInstrument, include_lookups=True)
        self.metadata_obj.create_all(self.engine)
