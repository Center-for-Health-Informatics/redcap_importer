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
