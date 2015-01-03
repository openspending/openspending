# widgets config
import logging
from urlparse import urljoin

from flask import current_app
from flask.ext.babel import gettext as _

log = logging.getLogger(__name__)


def get_widget(name, force=False):
    """ Get a dict to describe various properties of a named widget. """
    if not force and name not in list_widgets():
        raise ValueError(_("No widget named '%s' exists.") % name)

    base_url = current_app.config.get('WIDGETS_BASE')
    prefix = urljoin(base_url, name)

    widget_class = ''.join([p.capitalize() for p in name.split('_')])
    widget_class = 'OpenSpending.' + widget_class
    return {
        'js': '%s/main.js' % prefix,
        'base': prefix,
        'class_name': widget_class,
        'name': name,
        'preview': prefix + '/preview.png'
    }


def list_widgets():
    """ List of widgets registered in configuration file. """
    widgets = current_app.config.get('WIDGETS', [])
    return map(lambda w: w.strip(), widgets)
