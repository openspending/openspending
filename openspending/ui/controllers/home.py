import logging
import random

from pylons import request, response, tmpl_context as c, url, config
from pylons.controllers.util import redirect
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

    def index(self):
        # subdomain override:
        if hasattr(c, 'dataset') and c.dataset:
            redirect(url(controller='dataset', action='view',
                         id=c.dataset['name']))
        featured_dataset = config.get("openspending.default_dataset")
        c.datasets = list(model.dataset.find())
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

    def govspending(self):
        return render('home/25kspending.html')

    def getinvolved(self):
        return render('home/getinvolved.html')

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
