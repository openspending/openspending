import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from paste.deploy.converters import asbool
from pylons.i18n import _
from colander import Invalid

from openspending import model
from openspending.model import Source, Run, meta as db
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import abort, require
from openspending.tasks import analyze_source, load_source

from openspending.ui.validation.source import source_schema

log = logging.getLogger(__name__)

class RunController(BaseController):

    def _get_run(self, dataset, source, id):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.source = Source.by_id(source)
        if c.source is None or c.source.dataset != c.dataset:
            abort(404, _("There is no source '%s'") % source)
        c.run = Run.by_id(id)
        if c.run is None or c.run.source != c.source:
            abort(404, _("There is no run '%s'") % id)

    def view(self, dataset, source, id, format='html'):
        self._get_run(dataset, source, id)

    def record(self, dataset, source, run, id, format='html'):
        pass

