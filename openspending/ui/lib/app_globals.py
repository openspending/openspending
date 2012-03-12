from pylons import config
from paste.deploy.converters import asbool

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
        self.site_slogan = config.get(
            'openspending.site_slogan',
            'Mapping the money.'
        )
        self.site_logo = config.get(
            'openspending.site_logo',
            '/images/datastore-logo.png'
        )
        self.default_dataset = config.get(
            'openspending.default_dataset',
            'cra'
        )
        self.wiki_link = config.get(
            'openspending.wiki_link',
            'http://wiki.openspending.org'
        )
        self.blog_link = config.get(
            'openspending.blog_link',
            'http://wheredoesmymoneygo.org/blog/'
        )
        self.api_link = config.get(
            'openspending.api_link',
            'http://wiki.openspending.org/API'
        )
        self.lists_link = config.get(
            'openspending.lists_link',
            'http://lists.okfn.org/mailman/listinfo/openspending-discuss'
        )
        self.forum_link = config.get('openspending.forum_link')
        self.sandbox_mode = asbool(config.get(
            'openspending.sandbox_mode',
            False
        ))

        self.script_root = config.get('openspending.script_root', '/static/js')
