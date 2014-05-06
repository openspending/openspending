from __future__ import absolute_import
import os

from celery import Celery
from celery import signals
from celery.bin import Option

from openspending.command import _configure_pylons

# Get celery broker and backend from the environment with localhost
# RabbitMQ (or other AMQP message queue on 5672) as default
BROKER = os.environ.get('BROKER_URL', 'amqp://guest:guest@localhost:5672//')
BACKEND = os.environ.get('BACKEND_BROKER_URL', BROKER)

# Create Celery app for tasks, this is imported where we set the tasks
# and used by the celery commandline tool
celery = Celery('openspending.tasks', broker=BROKER, backend=BACKEND,
                include=['openspending.tasks.generic',
                         'openspending.tasks.dataset'])

# Add a user option to celery where the configuration file for pylons
# can be provided.
celery.user_options['preload'].add(
    Option('-p', '--pylons-ini-file',
           help='Pylons .ini file to use for environment configuration'),
)


@signals.user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    """
    Parse user options for celery. It only configures the environment
    if a pylons ini file is provided, else it does nothing.
    """
    if 'pylons_ini_file' in options:
        # Get the filename of the pylons ini file provided
        pylons_config = os.path.realpath(options['pylons_ini_file'])
        # Configure the pylons environment with the pylons config
        _configure_pylons(pylons_config)
