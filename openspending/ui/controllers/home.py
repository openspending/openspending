import logging
import os
import subprocess

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from openspending.model.dataset import Dataset, DatasetTerritory
from openspending.lib.solr_util import dataset_entries
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib.base import BaseController
from openspending.ui.lib.helpers import flash_success
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)


class HomeController(BaseController):

    def index(self):
        # Get all of the datasets available to the account of the logged in
        # or an anonymous user (if c.account is None)
        c.datasets = Dataset.all_by_account(c.account)
        c.territories = DatasetTerritory.dataset_counts(c.datasets)

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
            from openspending._version import __version__
            return __version__

    def favicon(self):
        return redirect('/static/img/favicon.ico', code=301)

    def ping(self):
        from openspending.tasks.generic import ping
        ping.delay()
        flash_success(_("Sent ping!"))
        redirect('/')
