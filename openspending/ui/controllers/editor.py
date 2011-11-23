import logging
import json

from pylons.controllers.util import redirect
from pylons import request, tmpl_context as c
from pylons.i18n import _
from colander import Invalid

from openspending.model import meta as db
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import require, abort
from openspending.validation.model.currency import CURRENCIES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.mapping import mapping_schema
from openspending.validation.model.views import views_schema
from openspending.validation.model.common import ValidationState

log = logging.getLogger(__name__)

class EditorController(BaseController):

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        return render('editor/index.html')

    def core_edit(self, dataset, errors={}, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.currencies = sorted(CURRENCIES.items(), key=lambda (k,v): v)
        errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
        fill = c.dataset.dataset.copy()
        if errors:
            fill.update(request.params)
        return render('editor/core.html', form_errors=dict(errors), 
                form_fill=fill)

    def core_update(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        errors = {}
        try:
            schema = dataset_schema(ValidationState(c.dataset.data))
            data = schema.deserialize(request.params)
            data['name'] = c.dataset.name
            c.dataset.label = c.dataset.data['dataset']['label'] = \
                    data['label']
            c.dataset.currency = c.dataset.data['dataset']['currency'] = \
                    data['currency']
            c.dataset.description = c.dataset.data['dataset']['description'] = \
                    data['description']
            db.session.commit()
            h.flash_success(_("The dataset metadata has been updated."))
        except Invalid, i:
            errors = i.asdict()
        return self.core_edit(dataset, errors=errors)

    def dimensions_edit(self, dataset, errors={}, mapping=None, 
            format='html'):
        # FIXME: cannot see this when there are no sources.

        # TODO: handle columns and model guess coming from 
        # source. 
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        mapping = mapping or c.dataset.data.get('mapping', {})
        c.fill = {'mapping': json.dumps(mapping, indent=2)}
        c.errors = errors
        c.can_edit = not len(c.dataset)
        return render('editor/dimensions.html', form_fill=c.fill)
    
    def dimensions_update(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        if len(c.dataset):
            abort(400, _("You cannot edit the dimensions model when " \
                    "data is loaded for the dataset."))

        errors, mapping = {}, None
        try:
            mapping = json.loads(request.params.get('mapping'))
            schema = mapping_schema(ValidationState(c.dataset.data))
            c.dataset.data['mapping'] = schema.deserialize(mapping)
            # erm...
            c.dataset.drop()
            c.dataset.generate()
            db.session.commit()
            h.flash_success(_("The mapping has been updated."))
        except (ValueError, TypeError):
            abort(400, _("The mapping data could not be decoded as JSON!"))
        except Invalid, i:
            errors = i.asdict()
        return self.dimensions_edit(dataset, errors=errors, 
                mapping=mapping)
    
    def views_edit(self, dataset, errors={}, views=None, 
            format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        views = views or c.dataset.data.get('views', [])
        c.fill = {'views': json.dumps(views, indent=2)}
        c.errors = errors
        return render('editor/views.html', form_fill=c.fill)
    
    def views_update(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        errors, views = {}, None
        try:
            views = json.loads(request.params.get('views'))
            schema = views_schema(ValidationState(c.dataset.data))
            c.dataset.data['views'] = schema.deserialize(views)
            db.session.commit()
            h.flash_success(_("The views have been updated."))
        except (ValueError, TypeError):
            abort(400, _("The views could not be decoded as JSON!"))
        except Invalid, i:
            errors = i.asdict()
        return self.views_edit(dataset, errors=errors, views=views)

    def drop(self, dataset):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.dataset.drop()
        c.dataset.generate()
        db.session.commit()
        h.flash_success(_("The dataset has been cleared."))
        redirect(h.url_for(controller='editor', action='index', 
                           dataset=c.dataset.name))

    def publish(self, dataset):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        if not c.dataset.private:
            abort(400, _("This dataset is already public!"))
        c.dataset.private = False
        db.session.commit()
        public_url = h.url_for(controller='dataset', action='view', 
                           dataset=c.dataset.name, qualified=True)
        h.flash_success(_("Congratulations, the dataset has been " \
                "published. It is now available at: %s") % public_url)
        redirect(h.url_for(controller='editor', action='index', 
                           dataset=c.dataset.name))

    def retract(self, dataset):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        if c.dataset.private:
            abort(400, _("This dataset is already private!"))
        c.dataset.private = True
        db.session.commit()
        h.flash_success(_("The dataset has been retracted. " \
                "It is no longer visible to others."))
        redirect(h.url_for(controller='editor', action='index', 
                           dataset=c.dataset.name))

