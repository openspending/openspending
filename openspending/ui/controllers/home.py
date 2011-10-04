import logging
import os
import random
import subprocess

from pylons import request, response, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending import model
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IDatasetController
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.helpers import flash_success, flash_error

log = logging.getLogger(__name__)


class HomeController(BaseController):

    extensions = PluginImplementations(IDatasetController)

    @beaker_cache(invalidate_on_startup=True,
           cache_response=False,
           query_args=True)
    def index(self):
        featured_dataset = config.get("openspending.default_dataset")
        c.dataset = filter(lambda x: x['name'] == featured_dataset, c.datasets)
        if c.dataset:
            c.dataset = c.dataset[0]
        elif c.datasets:
            c.dataset = c.datasets[0]
        else:
            c.dataset = None

        c.template = 'home/index.html'

        if c.dataset:
            c.num_entries = model.entry.find({"dataset.name": c.dataset['name']}).count()

            views.handle_request(request, c, c.dataset)

            for item in self.extensions:
                item.read(c, request, response, c.dataset)

        return render(c.template)

    def index_subdomain(self):
        if hasattr(c, 'dataset') and c.dataset:
            redirect(url(controller='dataset',
                         action='view',
                         name=c.dataset['name'],
                         sub_domain=None))
        else:
            redirect(url(controller='home',
                         action='index',
                         sub_domain=None))

    def getinvolved(self):
        return render('home/getinvolved.html')

    def reporterror(self):
        return render('home/reporterror.html')

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
