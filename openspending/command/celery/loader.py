from celery.loaders.base import BaseLoader
from celery.schedules import crontab

from pylons import config

to_pylons = lambda x: x.replace('_', '.').lower()

LIST_PARAMS = """CELERY_IMPORTS ADMINS ROUTES""".split()

SCHEDULE = {
    "analyze_all": {
        "task": "openspending.tasks.analyze_all_sources",
        "schedule": crontab(hour=3, minute=30),
        "args": ()
    },
    "clean_sessions": {
        "task": "openspending.tasks.clean_sessions",
        "schedule": crontab(hour=2, minute=30),
        "args": ()
    },
}


class PylonsSettingsProxy(object):

    """Pylons Settings Proxy

    Proxies settings from pylons.config

    """

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        if key == 'CELERYBEAT_SCHEDULE':
            return SCHEDULE
        pylons_key = to_pylons(key)
        value = config[pylons_key]
        if key in LIST_PARAMS:
            return value.split()
        return value

    def __setattr__(self, key, value):
        pylons_key = to_pylons(key)
        config[pylons_key] = value


class PylonsLoader(BaseLoader):

    """Pylons celery loader

    Maps the celery config onto pylons.config

    """

    def read_configuration(self):
        self.configured = True
        return PylonsSettingsProxy()

    def on_worker_init(self):
        """
        Import task modules.
        """
        self.import_default_modules()
