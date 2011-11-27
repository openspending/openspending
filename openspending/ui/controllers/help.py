import logging
import os
import random
import subprocess

from pylons import request, response, tmpl_context as c
from pylons import app_globals, url, config
from pylons.controllers.util import redirect, abort
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, render, require
from openspending.ui.lib.helpers import flash_success, flash_error

log = logging.getLogger(__name__)


class HelpController(BaseController):

    def page(self, path):
        suffix = 'help/%s' % path
        for path in app_globals.genshi_loader.search_path:
            filename = os.path.normpath(os.path.join(path, suffix))
            if not (filename.startswith(path)
                    and os.path.exists(filename)):
                continue
            return render(suffix)
        abort(404, "Sorry, the selected help file could not be found")

