from celery.loaders.base import BaseLoader
from pylons import config

to_pylons = lambda x: x.replace('_','.').lower()

LIST_PARAMS = """CELERY_IMPORTS ADMINS ROUTES""".split()


class PylonsSettingsProxy(object):
    """Pylons Settings Proxy

    Proxies settings from pylons.config

    """
    def __getattr__(self, key):
        pylons_key = to_pylons(key)
        try:
            value = config[pylons_key]
            if key in LIST_PARAMS: return value.split()
            return value
        except KeyError:
            raise AttributeError(pylons_key)
    
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

