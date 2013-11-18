import logging
import os
import random
import subprocess
from datetime import datetime

from pylons import request, response, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.model import Dataset
from openspending.lib.solr_util import dataset_entries
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.helpers import flash_success, flash_error
from openspending.ui.lib import helpers as h
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)

class HomeController(BaseController):

    def index(self):
        # Get all of the datasets available to the account of the logged in
        # or an anonymous user (if c.account is None)
        c.datasets = Dataset.all_by_account(c.account)

        c.num_entries = dataset_entries(None)
        return templating.render('home/index.html')

    def set_locale(self):
        locale = request.params.get('locale')
        if locale is not None:
            set_session_locale(locale)

    def version(self):
        cwd = os.path.dirname(__file__)
        process = subprocess.Popen('git rev-parse --verify HEAD'.split(' '),
                                   cwd=cwd,
                                   stdout=subprocess.PIPE)
        output = process.communicate()[0]
        if process.returncode == 0:
            return output
        else:
            import openspending.version
            return openspending.version.__version__

    def favicon(self):
        return redirect('/static/img/favicon.ico', code=301)

    def ping(self):
        from openspending.tasks import ping
        ping.delay()
        flash_success(_("Sent ping!"))
        redirect('/')
