import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.i18n import _
from routes import url_for

from openspending import model
from openspending.lib.util import deep_get
from openspending.logic.dimension import dataset_dimensions
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IEntryController
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.browser import Browser
from openspending.ui.lib.restapi import RestAPIMixIn

log = logging.getLogger(__name__)

class EntryController(BaseController, RestAPIMixIn):

    extensions = PluginImplementations(IEntryController)
    model = model.entry

    def _view_html(self, entry):
        c.entry = entry

        c.id = c.entry.get('_id')
        c.from_ = c.entry.get('from')
        c.to = c.entry.get('to')
        c.dataset = model.entry.get_dataset(entry)
        c.currency = c.entry.get('currency', c.dataset.get('currency')).upper()
        c.amount = c.entry.get('amount')
        c.time = c.entry.get('time')
        c.flags = c.entry.get("flags")

        c.custom_html = model.dataset.render_entry_custom_html(c.dataset, c.entry)

        excluded_keys = ('time', 'amount', 'currency', 'from',
                         'to', 'dataset', '_id', 'classifiers', 'name',
                         'classifier_ids', 'description')

        c.extras = {}
        if c.dataset:
            dataset_name = c.dataset["name"]
            dimensions = dataset_dimensions(dataset_name)
            c.desc = dict([(d.get('key'), d) for d in dimensions])
            for key in c.entry:
                if key in c.desc and \
                        not key in excluded_keys:
                    c.extras[key] = c.entry[key]

        c.template = 'entry/view.html'

        if 'departments' in c.dataset.get('name'):
            c.show_foi = True
        else:
            c.show_foi = False

        for item in self.extensions:
            item.read(c, request, response, c.entry)

        return render(c.template)

    def flag(self, id):
        entry = model.entry.get(id)
        if not entry:
            abort(404, _('Sorry, there is no entry with id %r') % id)
        if not c.account:
            abort(403, _('You need to have an account'))
        flag_name = request.params.get("flag", None)
        result = False
        try:
            result = flag.inc_flag(entry, flag_name, c.account)
        except KeyError:
            abort(400, _("Unknown Flag"))
        if not result:
            abort(409, _("This account already flagged this entry"))
        if request.headers.get("X-Requested-With", None) == "XMLHttpRequest":
            return "{'status': 'OK'}"
        return redirect(url_for(controller="entry", action="view", id=id))

