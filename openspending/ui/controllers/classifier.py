import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending import model
from openspending.plugins import PluginImplementations, IClassifierController
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.helpers import url_for
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.restapi import RestAPIMixIn

log = logging.getLogger(__name__)


class ClassifierController(BaseController, RestAPIMixIn):

    extensions = PluginImplementations(IClassifierController)

    model = model.Classifier

    def _entry_q(self, classifier):
        return model.Entry.find({'classifiers': c.classifier.id})

    def _make_browser(self):
        url = url_for(controller='classifier', action='entries',
                taxonomy=c.classifier.taxonomy,
                name=c.classifier.name)
        c.browser = Browser(request.params, url=url)
        c.browser.filter_by("+classifiers:%s" % c.classifier.id)
        c.browser.facet_by_dimensions()

    def view_by_taxonomy_name(self, taxonomy, name, format="html"):
        classifier = self._filter({"taxonomy": taxonomy, "name": name})
        if not classifier:
            abort(404)
        return self._handle_get(result=classifier[0], format=format)

    def _view_html(self, classifier):
        c.classifier = classifier

        handle_request(request, c, c.classifier)
        if c.view is None:
            self._make_browser()

        c.num_entries = self._entry_q(c.classifier).count()
        c.template = 'classifier/view.html'

        for item in self.extensions:
            item.read(c, request, response, c.classifier)

        return render(c.template)

    def entries(self, taxonomy, name, format='html'):
        c.classifier = model.Classifier.find_one({'taxonomy': taxonomy,
                                                  'name': name})
        if not c.classifier:
            abort(404, _('Sorry, there is no such classifier'))

        self._make_browser()
        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
            return
        return render('classifier/entries.html')
