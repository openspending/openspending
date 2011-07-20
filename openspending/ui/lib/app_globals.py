from pylons import config

class Globals(object):
    """\
    Globals acts as a container for objects available throughout the
    life of the application

    One instance of Globals is created during application
    initialization and is available during requests via the
    'app_globals' variable
    """

    def __init__(self):
        self.site_title = config.get('openspending.ui.site_title', 'Data Store')
        self.site_slogan = config.get(
            'openspending.ui.site_slogan',
            'Ever wondered what your taxes get spent on?'
        )
        self.site_logo = config.get(
            'openspending.ui.site_logo',
            '/images/datastore-logo.png'
        )

        self.default_dataset = config.get('openspending.ui.default_dataset', u'cra')
        self.banner_headline = config.get('openspending.ui.banner_headline', '')

        self.wiki_link = config.get(
            'openspending.ui.wiki_link',
            'http://wiki.openspending.org'
        )
        self.blog_link = config.get(
            'openspending.ui.blog_link',
            'http://wheredoesmymoneygo.org/blog/'
        )
        self.api_link = config.get(
            'openspending.ui.api_link',
            'http://wiki.openspending.org/API'
        )
        self.lists_link = config.get(
            'openspending.ui.lists_link',
            'http://lists.okfn.org/mailman/listinfo/openspending.ui-discuss'
        )
        self.forum_link = config.get('openspending.ui.forum_link')

