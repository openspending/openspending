import logging

from bson import ObjectId
from bson.errors import InvalidId

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending import model
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IEntityController
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.helpers import entity_slug, entity_url
from openspending.ui.lib.restapi import RestAPIMixIn
from openspending.ui.lib.views import handle_request


log = logging.getLogger(__name__)


class EntityController(BaseController, RestAPIMixIn):

    extensions = PluginImplementations(IEntityController)

    model = model.entity

    def view(self, id, slug='', format='html'):
        obj = model.entity.get(id)

        if not obj:
            abort(404, _('Sorry, there is no entity with id %r') % id)

        if format == 'html':
            # validate the slug and redirect to the current url if the slug
            # changed (e.g. fixed typo) with 301 - moved permanently
            if slug != entity_slug(obj):
                url = entity_url(obj)
                redirect(url, code=301)

        return self._view_no_redirect(id, format)

    @beaker_cache(invalidate_on_startup=True,
                  cache_response=False,
                  query_args=True)
    def _view_no_redirect(self, id, format):
        return self._view(id, format)

    def _make_browser(self):
        url = entity_url(c.entity, action='entries')
        c.browser = Browser(request.params, url=url)
        c.browser.filter_by(
            "(+to.id:%(_id)s OR +from.id:%(_id)s)" % {'_id': c.entity['_id']}
        )
        c.browser.facet_by_dimensions()

    def _view_html(self, entity):
        c.entity = entity

        handle_request(request, c, c.entity)
        if c.view is None:
            self._make_browser()

        c.num_entries = model.entry.find({'entities': entity['_id']}).count()
        c.template = 'entity/view.html'

        for item in self.extensions:
            item.read(c, request, response, c.entity)

        return render(c.template)

    @beaker_cache(invalidate_on_startup=True,
           cache_response=False,
           query_args=True)
    def entries(self, id, format='html'):
        c.entity = model.entity.get(id)
        if not c.entity:
            abort(404, _('Sorry, there is no entity named %r') % id)

        self._make_browser()
        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            return c.browser.to_csv()
        return render('entity/entries.html')
