import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import Invalid

from openspending import model
from openspending.model import Source, meta as db
from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import abort, require

log = logging.getLogger(__name__)

class SourceController(BaseController):

    def new(self, dataset, errors={}):
        self._get_dataset(dataset)
        pass

    def create(self, dataset):
        self._get_dataset(dataset)
        pass

    def view(self, dataset, id):
        self._get_dataset(dataset)
        source = Source.by_id(id)
        if source is None or source.dataset != c.dataset:
            abort(404, _("There is no source '%s'") % id)
        redirect(source.url)

    def load(self, dataset, id):
        self._get_dataset(dataset)
        pass

