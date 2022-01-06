 
The redcap_importer is a Django app that can be used to import a project from REDCap
into a relational database using the REDCap API. Data can be imported into any database
system supported by Django.

The tool will get the data dictionary for the project using the API and generate the Django ORM
code you need to build your database.

# Data Schema

The data schema in the database is specific to the REDCap project:

![database schemas](img/redcap_importer_schemas.png)

Some REDCap fields allow multiple values to be chosen. In this case, there will be a lookup table for each multi-choice field with a name like `my_instrument_my_field_lookup`.


# Set Up a Relational Database from a REDCap Project

### Prerequisites

You must already have a working Django project. See the [Django documentation](https://www.djangoproject.com/) for how to set up Django.

### 1. Install the App

Download the code from GitHub using pip
```
pip install git+https://github.com/Center-for-Health-Informatics/redcap_importer.git#egg=redcap_importer
```

Update your Django `settings.py`
```python
INSTALLED_APPS = [
    ...
    'redcap_importer',
]
```

### 2. (optional) Add redcap_importer views

This tool has views that allow you to browse imported REDCap data. These views aren't required to use the tool so this step is optional.

First add the redcap importer views to your `urls.py` file:
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('redcap_importer/', include(('redcap_importer.urls', 'redcap_importer'), namespace='redcap_importer')),
    ...
]
```

All views require Django login for security reasons. Django has a built-in authentication system but doesn't provide default login/logout views.

The easiest way to allow login is to use the login features already in the admin system. Set the admin login and logout URLs in your `settings.py` file.
```python
LOGIN_URL = '/admin/login'
LOGOUT_URL = '/admin/logout'
```
**NOTE:** The admin section only allows admin users to login. This setup would not be appropriate for a user-facing website. 

### 3. Set up the database

Run migrations to install redcap_importer system tables

```
python manage.py migrate
```



### 4. Set connection info for your REDCap project

Open your Django site and go to the Django admin section.

```
# create a superuser if none set yet
python manage.py createsuperuser

# start the built-in webserver
python manage.py runserver

# go to http://localhost:8000/admin and log in
```

You should be able to see the redcap_importer models you just created. 

First you must provide the API URL in the RedcapApiUrl table. 
- **name**: anything you want
- **url**:  the URL for the REDCap API
  - CCHMC: `https://redcap.research.cchmc.org/api/`
  - UC Health: `https://survey.uchealth.com/redcap/api/`

Then in the RedcapConnection table, provide information about your project
- **unique_name**: anything, but must be alphanumeric/dashes/underscores only
  - note: This unique_name will be used to reference the REDCap project everywhere else in this tool.
- **api_url**: Select the URL to use

You must also provide an API key from REDCap for this project. This can be obtained from the REDCap website. For security reasons, this goes into your Django `settings.py` file instead of into the database. Use the `RedcapConnection.unique_name` you created in step 5 to reference the project.

```python
REDCAP_API_TOKENS = {
	'project1': 'ABC...',
	'project2': 'DEF...',
	...
}
```

### 5. Create a new Django app where your database models will go

Give the app the same name as you used in `RedcapConnection.unique_name`
```
python manage.py startapp project1
```
And then add the app to your installed apps in `settings.py`
```python
INSTALLED_APPS = [
	...
	'redcap_importer',
	'project1',
]
```

### 6. (optional) Separate your application data from your patient data using a router

Not required, but it's often a good idea to keep your patient data in a separate database from the rest of your Django tables.

Set up a second database connection in your `settings.py` for patient data

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        },
        'patient_data': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'patient_data.sqlite3'),
        },
    }    

create a file `routers.py`

```
patient_data_apps = ['project1', 'project2', ...]
    
class CustomDatabaseRouter:

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to auth_db.
        """
        if model._meta.app_label in patient_data_apps:
            return 'patient_data'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to auth_db.
        """
        if model._meta.app_label in patient_data_apps:
            return 'patient_data'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        If not set, migrations will create duplicate tables in all databases.
        """
        if app_label in patient_data_apps:
            return db == 'patient_data'
        return db == 'default'
```


Give Django the path to your router in `settings.py`    
```
DATABASE_ROUTERS = ['mysite.routers.CustomDatabaseRouter']
```

### 7. Set up the database for your project

See a list of all projects you have set up
```python
python manage.py redcap_list_connections
```

Get the latest data dictionary for your project
```python
python manage.py redcap_get_dd project1
```

Use the data dictionary to create the model code that will go into `project1/models.py`
```python
# output model code for project1 to stdout
python manage.py redcap_write_models project1

# this code can be written directly to the models.py file for your app
python manage.py redcap_write_models project1 > project1/models.py
```
**NOTE:** Sometimes writing the output of redcap_write_models directly to the models.py file causes an error `source code string cannot contain null bytes`. If you encounter this error, write the output to stdout and manually copy and paste it into your models.py file. 

Create the database tables for your new models
```python
python manage.py makemigrations project1
python manage.py migrate

# if you have multiple databases, run migrations for all
python manage.py migrate --database=patient_data
```




# Load Data from REDCap into Your Database

Once your database is set up, you can load data anytime using the provided script

```
python manage.py redcap_load_data project1
```
**NOTE:** This will take from a minute up to several hours depending on the size of your database.

# Additional Tasks

## How do I load partial data?

If you don't want to load the entire REDCap project (in order to save time), you can specify the instruments using the REDCap Connections model in the Django admin.

- check the partial_load box to set to true

- provide the names of the instruments you want to include. All other instruments will be ignored.

NOTE: The database schema for the entire database is still created. But during the ETL the data will not be loaded.

## How do I customize the database models that were automatically created?

Don't do this. The data load process depends on the database models staying set up how they are. If you need your database set up differently, consider creating a separate database and using these as staging tables.

## How do I handle changes to the original REDCap project?

If the data dictionary for the REDCap project is changed after you've set up your database, it may break the ETL.

- changes that will break the ETL:
  - an instrument or field is renamed or deleted
  - new REDCap events are added (only applies to longitudinal projects)
- changed that will not break the ETL:
  - new instruments or fields are added (but this new data won't be imported without an update)

You can get a list of all changes since your last imported the data dictionary

```
python manage.py redcap_change_report project1
```

To Update your database with the latest version of the REDCap project:

#### 1. import the data dictionary again
```
python manage.py redcap_get_dd project1
```

#### 2. Update your Django models and database

```
python manage.py redcap_write_models project1 > project1/models.py
python manage.py makemigrations project1
python manage.py migrate
```

#### 3. Redownload the latest data

```
python manage.py redcap_load_data
```













