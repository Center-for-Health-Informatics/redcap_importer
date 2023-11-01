from django.conf import settings


# don't edit this directly, each setting can be overridden using the Django settings
# this file makes a useful reference for all chiron-specific settings and their default
# values


def get_setting(setting_name, alt):
    if hasattr(settings, setting_name):
        return getattr(settings, setting_name)
    return alt


REDCAP_DATA_DICT_FIXTURE_PATH = get_setting(
    "REDCAP_DATA_DICT_FIXTURE_PATH", "redcap_fixtures.json"
)
"""
The location where data dict backup fixture will be saved/restored using management commands
redcap_backup_dd and redcap_restore_dd.
"""


REDCAP_API_TOKENS = get_setting("REDCAP_API_TOKENS", {})
"""
A dict with key->value pairs for each REDCap project RedcapConnection.unique_name->API token.
"""

REDCAP_SQL_ALCHEMY_CONNECTION_STRING = get_setting("REDCAP_SQL_ALCHEMY_CONNECTION_STRING", None)
"""
The connection string for the database where the actual redcap snapshot will be stored. This is
separate from the database where application data and the data dictionary are stored. Supported
databases are sqlite3, postgresql, and sql_server.

examples: 
"postgresql://myuser:mypassword@localhost:5432/my_database"
"sqlite:///C:\\path\\to\\foo.db"
"""
