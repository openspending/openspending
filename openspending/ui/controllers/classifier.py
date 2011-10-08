import logging

from pylons import request, response, tmpl_context as c
from pylons.decorators.cache import beaker_cache
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending import model
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IClassifierController
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.helpers import url_for
from openspending.ui.lib.browser import Browser
from openspending.lib.csvexport import write_csv
from openspending.ui.lib.jsonp import to_jsonp

log = logging.getLogger(__name__)


class ClassifierController(BaseController):

    extensions = PluginImplementations(IClassifierController)

    def _get_classifier(self, dataset, taxonomy, name):
        self._get_dataset(dataset)
        for dimension in c.dataset.compounds:
            if dimension.taxonomy == taxonomy:
                members = list(dimension.members(dimension.alias.c.name==name,
                    limit=1))
                if not len(members):
                    abort(404, _('Sorry, there is no taxonomy member named %r')
                            % name)
                c.classifier = members.pop()
                return
        abort(404, _('Sorry, there is no taxonomy named %r') % taxonomy)


    @beaker_cache(invalidate_on_startup=True,
                  cache_response=False,
                  query_args=True)
    def view(self, dataset, taxonomy, name, format="html"):
        self._get_classifier(dataset, taxonomy, name)
        c.num_entries = -1

        handle_request(request, c, c.classifier)
        if c.view is None:
            self._make_browser()

        for item in self.extensions:
            item.read(c, request, response, c.classifier)

        if format == 'json':
            return to_jsonp(c.classifier)
        elif format == 'csv':
            write_csv([c.dataset.as_dict()], response)
            return
        else:
            return render('classifier/view.html')


    @beaker_cache(invalidate_on_startup=True,
                  cache_response=False,
                  query_args=True)
    def entries(self, dataset, taxonomy, name, format='html'):
        self._get_classifier(dataset, taxonomy, name)

        self._make_browser()
        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
        else:
            return render('classifier/entries.html')


    def _make_browser(self):
        url = url_for(controller='classifier', action='entries',
                dataset=c.dataset.name,
                taxonomy=c.classifier['taxonomy'],
                name=c.classifier['name'])
        c.browser = Browser(c.dataset, request.params, url=url)
        dimensions = []
        for dimension in c.dataset.dimensions:
            if isinstance(dimension, model.CompoundDimension) and \
                    dimension.taxonomy == c.classifier['taxonomy']:
                dimensions.append('%s:%s' % (dimension.name, 
                                             c.classifier['name']))
        c.browser.filter_by("+(%s)" % ' OR '.join(dimensions))
        c.browser.facet_by_dimensions()
