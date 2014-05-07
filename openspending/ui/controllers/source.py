import logging

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from paste.deploy.converters import asbool
from pylons.i18n import _
from colander import Invalid

from openspending.model import meta as db
from openspending.model.source import Source

from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController
from openspending.ui.lib.base import abort, require
from openspending.tasks.dataset import analyze_source, load_source
from openspending.ui.alttemplates import templating

from openspending.ui.validation.source import source_schema

log = logging.getLogger(__name__)


class SourceController(BaseController):

    def new(self, dataset, errors={}):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        params_dict = dict(request.params) if errors else {}
        return templating.render('source/new.html', form_errors=errors,
                                 form_fill=params_dict)

    def create(self, dataset):
        self._get_dataset(dataset)
        require.dataset.update(c.dataset)
        try:
            schema = source_schema()
            data = schema.deserialize(request.params)
            source = Source(c.dataset, c.account, data['url'])
            db.session.add(source)
            db.session.commit()
            analyze_source.apply_async(args=[source.id], countdown=2)
            h.flash_success(_("The source has been created."))
            redirect(h.url_for(controller='editor', action='index',
                               dataset=c.dataset.name))
        except Invalid as i:
            errors = i.asdict()
            errors = [(k[len('source.'):], v) for k, v in errors.items()]
            return self.new(dataset, dict(errors))

    def index(self, dataset, format='json'):
        self._get_dataset(dataset)
        return to_jsonp([src.as_dict() for src in c.dataset.sources])

    def _get_source(self, dataset, id):
        self._get_dataset(dataset)
        c.source = Source.by_id(id)
        if c.source is None or c.source.dataset != c.dataset:
            abort(404, _("There is no source '%s'") % id)

    def view(self, dataset, id):
        self._get_source(dataset, id)
        redirect(c.source.url)

    def load(self, dataset, id):
        """
        Load the dataset into the database. If a url parameter 'sample'
        is provided then its value is converted into a boolean. If the value
        equals true we only perform a sample run, else we do a full load.
        """

        # Get our source (and dataset)
        self._get_source(dataset, id)

        # We require that the user can update the dataset
        require.dataset.update(c.dataset)

        # If the source is already running we flash an error declaring that
        # we're already running this source
        if c.source.is_running:
            h.flash_error(_("Already running!"))
        # If the source isn't already running we try to load it (or sample it)
        else:
            try:
                sample = asbool(request.params.get('sample', 'false'))
                load_source.delay(c.source.id, sample)
                # Let the user know we're loading the source
                h.flash_success(_("Now loading..."))
            except Exception as e:
                abort(400, e)

        # Send the user to the editor index page for this dataset
        redirect(h.url_for(controller='editor', action='index',
                           dataset=c.dataset.name))

    def delete(self, dataset, id):
        # Get our source (and dataset)
        self._get_source(dataset, id)

        # We require that the user can update the dataset
        require.dataset.update(c.dataset)

        # Delete the source if hasn't been sucessfully loaded
        # If it is successfully loaded we don't return an error
        # message because the user is then going around the normal
        # user interface
        if not c.source.successfully_loaded:
            db.session.delete(c.source)
            db.session.commit()

        redirect(h.url_for(controller='editor', action='index',
                           dataset=c.dataset.name))

    def analysis(self, dataset, source, format='json'):
        self._get_source(dataset, source)
        return to_jsonp(c.source.analysis)
