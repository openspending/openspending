
SECRET_KEY = 'foo'
DEBUG = True

SITE_TITLE = 'OpenSpending'

SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/openspending'
#SQLALCHEMY_ECHO = True

SOLR_URL = 'http://localhost:8983/solr/openspending'

BABEL_DEFAULT_LOCALE = 'en'

SUBSCRIBE_COMMUNITY = 'http://lists.okfn.org/mailman/subscribe/openspending'
SUBSCRIBE_DEVELOPER = 'http://lists.okfn.org/mailman/subscribe/openspending-dev'

MAIL_FORM = 'noreply@openspending.org'

CACHE = True
CACHE_TYPE = 'simple'

WIDGETS_BASE = '/static/openspendingjs/widgets/'
WIDGETS = ['treemap', 'bubbletree', 'aggregate_table']
