import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from openspending import model
from openspending.model import Source, Run, LogRecord, meta as db
from openspending.ui.lib import helpers as h
from openspending.ui.lib.page import Page
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import abort, require

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
        system = c.run.records.filter_by(category=LogRecord.CATEGORY_SYSTEM)
        c.num_system = system.count()
        c.system_page = Page(system.order_by(LogRecord.timestamp.asc()), 
                page=self._get_page('system_page'),
                items_per_page=10)
        data = c.run.records.filter_by(category=LogRecord.CATEGORY_DATA)
        c.num_data = data.count()
        c.data_page = Page(data.order_by(LogRecord.timestamp.asc()), 
                page=self._get_page('data_page'),
                items_per_page=20)
        return render('run/view.html')


