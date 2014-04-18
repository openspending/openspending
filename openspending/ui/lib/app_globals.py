from pylons import config
from paste.deploy.converters import asbool
from economics import Inflation


class Globals(object):

    """\
    Globals acts as a container for objects available throughout the
    life of the application

    One instance of Globals is created during application
    initialization and is available during requests via the
    'app_globals' variable
    """

    def __init__(self):
        self.debug = asbool(config.get('debug', False))

        self.site_title = config.get(
            'openspending.site_title',
            'OpenSpending'
        )
        self.cache_enabled = asbool(config.get(
            'openspending.cache_enabled',
            True
        ))

        self.script_root = config.get('openspending.script_root', '/static/js')

        if asbool(config.get('openspending.fake_inflation', False)):
            from .fake_inflation import Inflation as FakeInflation
            self.inflation = FakeInflation()
        else:
            self.inflation = Inflation()
