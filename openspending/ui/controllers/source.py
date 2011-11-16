import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import Invalid

from openspending import model
from openspending.model import Source, meta as db
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import abort, require

from openspending.validation.source import source_schema

log = logging.getLogger(__name__)

class SourceController(BaseController):

    def new(self, dataset, errors={}):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        return render('source/new.html', form_errors=errors,
                form_fill=request.params if errors else None)

    def create(self, dataset):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        try:
            schema = source_schema()
            data = schema.deserialize(request.params)
            source = Source(c.dataset, c.account, data['url'])
            db.session.add(source)
            db.session.commit()
            h.flash_success(_("The source has been created."))
            redirect(h.url_for(controller='editor', action='index', 
                               dataset=c.dataset.name))
        except Invalid, i:
            errors = i.asdict()
            errors = [(k[len('source.'):], v) for k, v \
                    in errors.items()]
            return self.new(dataset, dict(errors))

    def view(self, dataset, id):
        self._get_dataset(dataset)
        source = Source.by_id(id)
        if source is None or source.dataset != c.dataset:
            abort(404, _("There is no source '%s'") % id)
        redirect(source.url)

    def load(self, dataset, id):
        self._get_dataset(dataset)
        pass

