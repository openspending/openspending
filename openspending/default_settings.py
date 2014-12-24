from kombu import Exchange, Queue

SECRET_KEY = 'foo'
DEBUG = True

SITE_TITLE = 'OpenSpending'

SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/openspending'
SOLR_URL = 'http://localhost:8983/solr'

BABEL_DEFAULT_LOCALE = 'en'

SUBSCRIBE_COMMUNITY = 'http://lists.okfn.org/mailman/subscribe/openspending'
SUBSCRIBE_DEVELOPER = 'http://lists.okfn.org/mailman/subscribe/openspending-dev'

MAIL_FORM = 'noreply@openspending.org'

CACHE = True
CACHE_TYPE = 'simple'

WIDGETS_BASE = '/static/openspendingjs/widgets/'
WIDGETS = ['treemap', 'bubbletree', 'aggregate_table']

## Image uploads directory, needs to be read/writeable by frontend.
UPLOADS_DEFAULT_DEST = '/tmp/openspending-uploads'

## Worker queue configuration.
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# If you set ``EAGER``, processing will happen inline.
CELERY_ALWAYS_EAGER = False
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERY_DEFAULT_QUEUE = 'analysis'
CELERY_QUEUES = (
    Queue('analysis', Exchange('openspending'), routing_key='openspending'),
    Queue('loading', Exchange('openspending'), routing_key='openspending'),
)

CELERY_ROUTES = {
    'openspending.tasks.analyze_all_sources': {
        'queue': 'analysis'
    },
    'openspending.tasks.analyze_source': {
        'queue': 'analysis'
    },
    'openspending.tasks.analyze_budget_data_package': {
        'queue': 'analysis'
    },
    'openspending.tasks.load_source': {
        'queue': 'loading'
    },
    'openspending.tasks.load_budgetdatapackage': {
        'queue': 'loading'
    },
    'openspending.tasks.index_dataset': {
        'queue': 'loading'
    },
}
