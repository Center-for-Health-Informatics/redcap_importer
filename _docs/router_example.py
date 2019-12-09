

# A good configuration will put application data and patient data into separate databases or
# separate schemas within the same database.
#
# The router below will put the RedcapImporter metadata tables along with the Django tables into
# the default database (cicrl.public).  And all patient data goes into the 'patient_data' database (ciclr.patient_data).


### in Django settings #####################################################

DATABASES = {
    'default': {
        'NAME': 'cicrl',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'username',
        'PASSWORD': '',
    },
    'patient_data': {
        'NAME': 'cicrl',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'username',
        'PASSWORD': '',
        'OPTIONS' : {
            'options': '-c search_path=patient_data'
        }
    },
}

DATABASE_ROUTERS = ['project.router.CustomDatabaseRouter']

### project/router.py #######################################################

class CustomDatabaseRouter:
    """
    A router to control all database operations on models in the
    auth application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to auth_db.
        """
        if model._meta.app_label in ['cicrl_operations', 'cicrl_daily_tracker', 'cicrl_intake_plus_daily']:
            return 'patient_data'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to auth_db.
        """
        if model._meta.app_label in ['cicrl_operations', 'cicrl_daily_tracker', 'cicrl_intake_plus_daily']:
            return 'patient_data'
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        If not set, migrations will create duplicate tables in all databases.
        """
        if app_label in ['cicrl_operations', 'cicrl_daily_tracker', 'cicrl_intake_plus_daily']:
            return db == 'patient_data'
        return db == 'default'
    
    
    
    
    
    
    
    
    
    
    