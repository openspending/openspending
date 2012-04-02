import logging
import json
import math

from pylons.controllers.util import redirect
from pylons import request, tmpl_context as c
from pylons.i18n import _
from colander import Invalid

from openspending.model import meta as db
from openspending.lib import solr_util as solr
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.base import require, abort
from openspending.ui.lib.cache import AggregationCache
from openspending.reference.currency import CURRENCIES
from openspending.reference.country import COUNTRIES
from openspending.reference.language import LANGUAGES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.mapping import mapping_schema
from openspending.validation.model.views import views_schema
from openspending.validation.model.common import ValidationState

log = logging.getLogger(__name__)


class EditorController(BaseController):

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.entries_count = len(c.dataset)
        c.has_sources = c.dataset.sources.count() > 0
        c.source = c.dataset.sources.first()
        c.index_count = solr.dataset_entries(c.dataset.name)
        c.index_percentage = 0 if not c.entries_count else \
            int((float(c.index_count) / float(c.entries_count)) * 1000)
        return render('editor/index.html')

    def core_edit(self, dataset, errors={}, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        c.key_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if k],
                key=lambda (k, v): v)
        c.all_currencies = sorted([(r, n) for (r, (n, k)) in CURRENCIES.items() if not k],
                key=lambda (k, v): v)
        c.languages = sorted(LANGUAGES.items(), key=lambda (k, v): v)
        c.territories = sorted(COUNTRIES.items(), key=lambda (k, v): v)

        if 'time' in c.dataset:
            c.available_times = [m['time']['year'] for m in c.dataset['time'].members()]
            c.available_times = sorted(set(c.available_times), reverse=True)
        else:
            c.available_times = []

        errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
        fill = c.dataset.as_dict()
        if errors:
            fill.update(request.params)
        return render('editor/core.html', form_errors=dict(errors),
                form_fill=fill)

    def core_update(self, dataset, format='html'):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        errors = {}
        try:
            schema = dataset_schema(ValidationState(c.dataset.model))
            data = dict(request.params)
            data['territories'] = request.params.getall('territories')
            data['languages'] = request.params.getall('languages')
            data = schema.deserialize(data)
            c.dataset.label = data['label']
            c.dataset.currency = data['currency']
            c.dataset.description = data['description']
            c.dataset.default_time = data['default_time']
            c.dataset.territories = data['territories']
            c.dataset.languages = data['languages']
            db.session.commit()
            h.flash_success(_("The dataset has been updated."))
        except Invalid, i:
            errors = i.asdict()
        return self.core_edit(dataset, errors=errors)

    def dimensions_edit(self, dataset, errors={}, mapping=None,
            format='html', saved=False):

        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        # TODO: really split up dimensions and mapping editor.
        c.source = c.dataset.sources.first()
        if c.source is None:
            return render('editor/dimensions_errors.html')
        mapping = mapping or c.dataset.data.get('mapping', {})
        if not len(mapping) and c.source and 'mapping' in c.source.analysis:
            mapping = c.source.analysis['mapping']
        c.fill = {'mapping': json.dumps(mapping, indent=2)}
        c.errors = errors
        c.saved = saved
        if len(c.dataset):
            return render('editor/dimensions_errors.html')
        return render('editor/dimensions.html', form_fill=c.fill)

    def dimensions_update(self, dataset, format='html'):
        self._get_dataset(dataset)

        require.dataset.update(c.dataset)
        if len(c.dataset):
            abort(400, _("You cannot edit the dimensions model when " \
                    "data is loaded for the dataset."))

        errors, mapping, saved = {}, None, False
        try:
            mapping = json.loads(request.params.get('mapping'))
            model = c.dataset.model
            model['mapping'] = mapping
            schema = mapping_schema(ValidationState(model))
            new_mapping =  schema.deserialize(mapping)
            c.dataset.data['mapping'] = new_mapping
            c.dataset.drop()
            c.dataset._load_model()
            c.dataset.generate()
            db.session.commit()
            #h.flash_success(_("The mapping has been updated."))
            saved = True
        except (ValueError, TypeError, AttributeError):
            abort(400, _("The mapping data could not be decoded as JSON!"))
        except Invalid, i:
            errors = i.asdict()
        return self.dimensions_edit(dataset, errors=errors, 
                mapping=mapping, saved=saved)
    
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
            schema = views_schema(ValidationState(c.dataset.model))
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
        solr.drop_index(c.dataset.name)
        c.dataset.init()
        c.dataset.generate()
        AggregationCache(c.dataset).invalidate()
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
        AggregationCache(c.dataset).invalidate()
        db.session.commit()
        h.flash_success(_("The dataset has been retracted. " \
                "It is no longer visible to others."))
        redirect(h.url_for(controller='editor', action='index', 
                           dataset=c.dataset.name))

    def delete(self, dataset):
        self._get_dataset(dataset)
        require.dataset.delete(c.dataset)
        c.dataset.drop()
        solr.drop_index(c.dataset.name)
        db.session.delete(c.dataset)
        db.session.commit()
        h.flash_success(_("The dataset has been deleted."))
        redirect(h.url_for(controller='dataset', action='index'))
