import logging
import os
import random
import subprocess

from pylons import request, response, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, render, require
from openspending.ui.lib.helpers import flash_success, flash_error

log = logging.getLogger(__name__)


class HomeController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    def index(self):
        # TODO decide if we want this.
        #featured_dataset = config.get("openspending.default_dataset")
        return render('home/index.html')

    def index_subdomain(self):
        if hasattr(c, 'dataset') and c.dataset:
            require.dataset.read(c.dataset)
            redirect(url(controller='dataset',
                         action='view',
                         name=c.dataset['name'],
                         sub_domain=None))
        else:
            redirect(url(controller='home',
                         action='index',
                         sub_domain=None))

    def locale(self):
        return_to = request.params.get('return_to', '/')
        locale = request.params.get('locale')
        if locale is not None:
            flash_success(_("Language has been set to: English"))
            set_session_locale(locale)
        else:
            flash_error(_("No language given!"))
        return_to += '&' if '?' in return_to else '?'
        # hack to prevent next page being cached
        return_to += '__cache=%s' % int(random.random() * 100000000)
        redirect(return_to.encode('utf-8'))

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

    def ping(self):
        from openspending.tasks import ping
        ping.delay()
        flash_success(_("Sent ping!"))
        redirect('/')
