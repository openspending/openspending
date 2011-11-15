import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _
from colander import Invalid

from openspending import model
from openspending.model import Dataset, meta as db
from openspending.lib.csvexport import write_csv
from openspending.ui.lib.jsonp import to_jsonp
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import abort, require
from openspending.ui.lib.browser import Browser
from openspending.validation.currency import CURRENCIES
from openspending.validation.dataset import Dataset as DatasetSchema

log = logging.getLogger(__name__)

class EditorController(BaseController):


    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        return render('editor/index.html')


    def core_edit(self, dataset, errors={}, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.currencies = [(k, v['name']) for k,v in CURRENCIES.items()]
        c.currencies = sorted(c.currencies, key=lambda (k,v): v)
        fill = c.dataset.dataset.copy()
        if errors:
            fill.update(request.params)
        return render('editor/core.html', form_errors=errors, 
                form_fill=fill)


    def core_update(self, dataset, errors={}, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        errors = {}
        try:
            schema = DatasetSchema()
            data = schema.deserialize(request.params)
            data['name'] = c.dataset.name
            c.dataset.label = c.dataset.data['dataset']['label'] = \
                    data['label']
            c.dataset.currency = c.dataset.data['dataset']['currency'] = \
                    data['currency']
            c.dataset.description = c.dataset.data['dataset']['description'] = \
                    data['description']
            db.session.commit()
            h.flash_success(_("The dataset has been updated."))
        except Invalid, i:
            errors = i.asdict()
        return self.core_edit(dataset, errors=errors)
