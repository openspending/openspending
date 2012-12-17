import logging
import os
import random
import subprocess
from datetime import datetime

from pylons import request, response, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.lib.solr_util import dataset_entries
from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, render, require, \
        sitemap, sitemapindex
from openspending.ui.lib.helpers import flash_success, flash_error
from openspending.ui.lib.content import ContentResource
from openspending.ui.lib import helpers as h

log = logging.getLogger(__name__)

class HomeController(BaseController):

    def index(self):
        c.blog = ContentResource('blog', 'home.html')
        c.num_entries = dataset_entries(None)
        return render('home/index.html')

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

    def sitemap_index(self):
        sitemaps = [{'loc': h.url_for(controller='home', action='sitemap', qualified=True),
                     'lastmod': datetime.utcnow()}]
        for dataset in c.datasets:
            sitemaps.append({
                'loc': h.url_for(controller='dataset', action='sitemap',
                               dataset=dataset.name, qualified=True),
                'lastmod': dataset.updated_at
                })
            for ep in range(1, (len(dataset)/30000)+2):
                sitemaps.append({
                    'loc': h.url_for(controller='entry', action='sitemap',
                                   dataset=dataset.name, page=ep,
                                   qualified=True),
                    'lastmod': dataset.updated_at
                    })
            for dim in dataset.compounds:
                if dim.name == 'time':
                    continue
                sitemaps.append({
                    'loc': h.url_for(controller='dimension', action='sitemap',
                                   dataset=dataset.name, dimension=dim.name,
                                   qualified=True),
                    'lastmod': dataset.updated_at
                    })
        return sitemapindex(sitemaps)

    def sitemap(self):
        sections = ['blog', 'resources', 'about', 'help']
        base = h.url_for(controller='home', action='index', qualified=True)
        pages = []
        for section in sections:
            pages.append({
                'loc': base + section + '/index.html',
                'lastmod': datetime.utcnow(),
                'freq': 'daily',
                'priority': 0.9
                })
        return sitemap(pages)

    def favicon(self):
        return redirect('/static/img/favicon.ico', code=301)

    def ping(self):
        from openspending.tasks import ping
        ping.delay()
        flash_success(_("Sent ping!"))
        redirect('/')
