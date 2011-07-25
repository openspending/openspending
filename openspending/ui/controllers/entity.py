import logging

from bson import ObjectId
from bson.errors import InvalidId

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
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

    model = model.Entity

    def view(self, id, slug='', format='html'):
        # abort if we have no ObjectId. We don't want to
        # lookup by name.
        try:
            oid = ObjectId(id)
        except InvalidId:
            abort(404, _('Sorry, there is no %s with code %r') %
                  (self.model.__name__.lower(), id))

        if format == 'html':
            # validate the slug and redirect to the current url if the slug
            # changed (e.g. fixed typo) with 301 - moved permanently
            entity = self._get_by_id(oid)
            if slug != entity_slug(entity):
                url = entity_url(entity)
                redirect(url, code=301)

        return super(EntityController, self).view(id, format)

    def _entry_q(self, entity):
        return model.Entry.find({'entities': entity.id})

    def _make_browser(self):
        url = entity_url(c.entity, action='entries')
        c.browser = Browser(request.params, url=url)
        c.browser.filter_by("(+to.id:%s OR +from.id:%s)" % (c.entity.id,
                                                            c.entity.id))
        c.browser.facet_by_dimensions()

    def _view_html(self, entity):
        c.entity = entity

        handle_request(request, c, c.entity)
        if c.view is None:
            self._make_browser()

        c.num_entries = self._entry_q(c.entity).count()
        c.template = 'entity/view.html'

        for item in self.extensions:
            item.read(c, request, response, c.entity)

        return render(c.template)

    def entries(self, id, format='html'):
        c.entity = model.Entity.by_id(id)
        if not c.entity:
            abort(404, _('Sorry, there is no entity named %r') % id)

        self._make_browser()
        if format == 'json':
            return c.browser.to_jsonp()
        elif format == 'csv':
            c.browser.to_csv()
            return

        return render('entity/entries.html')
