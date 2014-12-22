import logging
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect
from flask.ext.babel import gettext as _
from colander import Invalid

from openspending.core import db
from openspending.model import Account, Run
from openspending.auth import require
from openspending.lib import solr_util as solr
from openspending.lib.helpers import url_for, obj_or_404
from openspending.lib.helpers import url_for, get_dataset
from openspending.lib.helpers import disable_cache, flash_error
from openspending.lib.helpers import flash_notice, flash_success
from openspending.lib.cache import AggregationCache, DatasetIndexCache
from openspending.reference.currency import CURRENCIES
from openspending.reference.country import COUNTRIES
from openspending.reference.category import CATEGORIES
from openspending.reference.language import LANGUAGES
from openspending.validation.model.dataset import dataset_schema
from openspending.validation.model.mapping import mapping_schema
from openspending.validation.model.views import views_schema
from openspending.validation.model.common import ValidationState

log = logging.getLogger(__name__)
blueprint = Blueprint('editor', __name__)


@disable_cache
@blueprint.route('/<dataset>/editor', methods=['GET'])
def index(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    c.entries_count = len(c.dataset)
    c.has_sources = c.dataset.sources.count() > 0
    c.source = c.dataset.sources.first()
    c.index_count = solr.dataset_entries(c.dataset.name)
    c.index_percentage = 0 if not c.entries_count else \
        int((float(c.index_count) / float(c.entries_count)) * 1000)
    return render_template('editor/index.html')


@disable_cache
@blueprint.route('/<dataset>/editor/core', methods=['GET'])
def core_edit(dataset, errors={}):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    c.key_currencies = sorted(
        [(r, n) for (r, (n, k)) in CURRENCIES.items() if k],
        key=lambda k_v: k_v[1])
    c.all_currencies = sorted(
        [(r, n) for (r, (n, k)) in CURRENCIES.items() if not k],
        key=lambda k_v1: k_v1[1])
    c.languages = sorted(LANGUAGES.items(), key=lambda k_v2: k_v2[1])
    c.territories = sorted(COUNTRIES.items(), key=lambda k_v3: k_v3[1])
    c.categories = sorted(CATEGORIES.items(), key=lambda k_v4: k_v4[1])

    if 'time' in c.dataset:
        c.available_times = [m['year']
                             for m in c.dataset['time'].members()]
        c.available_times = sorted(set(c.available_times), reverse=True)
    else:
        c.available_times = []

    errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
    fill = c.dataset.as_dict()
    if errors:
        fill.update(request.params)
    return render_template('editor/core.html', form_errors=dict(errors),
                             form_fill=fill)


@blueprint.route('/<dataset>/editor/core', methods=['POST'])
def core_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    errors = {}
    try:
        schema = dataset_schema(ValidationState(c.dataset.model))
        data = dict(request.params)
        data['territories'] = request.params.getall('territories')
        data['languages'] = request.params.getall('languages')
        data = schema.deserialize(data)
        c.dataset.label = data['label']
        c.dataset.currency = data['currency']
        c.dataset.category = data['category']
        c.dataset.description = data['description']
        c.dataset.default_time = data['default_time']
        c.dataset.territories = data['territories']
        c.dataset.languages = data['languages']
        db.session.commit()
        h.flash_success(_("The dataset has been updated."))
    except Invalid as i:
        errors = i.asdict()
    return self.core_edit(dataset, errors=errors)


@disable_cache
@blueprint.route('/<dataset>/editor/dimensions', methods=['GET'])
def dimensions_edit(dataset, errors={}, mapping=None,
                    saved=False):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    # TODO: really split up dimensions and mapping editor.
    c.source = c.dataset.sources.first()
    if c.source is None:
        return render_template('editor/dimensions_errors.html')
    mapping = mapping or c.dataset.data.get('mapping', {})
    if not len(mapping) and c.source and 'mapping' in c.source.analysis:
        mapping = c.source.analysis['mapping']
    c.fill = {'mapping': json.dumps(mapping, indent=2)}
    c.errors = errors
    c.saved = saved
    if len(c.dataset):
        return render_template('editor/dimensions_errors.html')
    return render_template('editor/dimensions.html', form_fill=c.fill)


@blueprint.route('/<dataset>/editor/dimensions', methods=['POST'])
def dimensions_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    if len(c.dataset):
        abort(400, _("You cannot edit the dimensions model when "
                     "data is loaded for the dataset."))

    errors, mapping, saved = {}, None, False
    try:
        mapping = json.loads(request.params.get('mapping'))
        model = c.dataset.model
        model['mapping'] = mapping
        schema = mapping_schema(ValidationState(model))
        new_mapping = schema.deserialize(mapping)
        c.dataset.data['mapping'] = new_mapping
        c.dataset.drop()
        c.dataset._load_model()
        c.dataset.generate()
        db.session.commit()
        # h.flash_success(_("The mapping has been updated."))
        saved = True
    except (ValueError, TypeError, AttributeError):
        abort(400, _("The mapping data could not be decoded as JSON!"))
    except Invalid as i:
        errors = i.asdict()
    return self.dimensions_edit(dataset, errors=errors,
                                mapping=mapping, saved=saved)


@disable_cache
@blueprint.route('/<dataset>/editor/templates', methods=['GET'])
def templates_edit(dataset, errors={}, values=None):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    c.fill = values or {'serp_title': c.dataset.serp_title,
                        'serp_teaser': c.dataset.serp_teaser}
    c.errors = errors
    return render_template('editor/templates.html', form_fill=c.fill)


@blueprint.route('/<dataset>/editor/templates', methods=['POST'])
def templates_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, values = {}, None
    try:
        values = dict(request.params.items())
        c.dataset.serp_title = values.get('serp_title', None)
        c.dataset.serp_teaser = values.get('serp_teaser', None)
        db.session.commit()
        h.flash_success(_("The templates have been updated."))
    except Invalid as i:
        errors = i.asdict()
    return self.templates_edit(dataset, errors=errors, values=values)


@disable_cache
@blueprint.route('/<dataset>/editor/views', methods=['GET'])
def views_edit(dataset, errors={}, views=None,
               format='html'):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    views = views or c.dataset.data.get('views', [])
    c.fill = {'views': json.dumps(views, indent=2)}
    c.errors = errors
    return render_template('editor/views.html', form_fill=c.fill)


@blueprint.route('/<dataset>/editor/views', methods=['POST'])
def views_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, views = {}, None
    try:
        views = json.loads(request.params.get('views'))
        schema = views_schema(ValidationState(c.dataset.model))
        c.dataset.data['views'] = schema.deserialize(views)
        db.session.commit()
        h.flash_success(_("The views have been updated."))
    except (ValueError, TypeError):
        abort(400, _("The views could not be decoded as JSON!"))
    except Invalid as i:
        errors = i.asdict()
    return self.views_edit(dataset, errors=errors, views=views)


@disable_cache
@blueprint.route('/<dataset>/editor/team', methods=['GET'])
def team_edit(dataset, errors={}, accounts=None):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    accounts = accounts or c.dataset.managers
    c.accounts = json.dumps([a.as_dict() for a in accounts], indent=2)
    c.errors = errors
    return render_template('editor/team.html')


@blueprint.route('/<dataset>/editor/team', methods=['POST'])
def team_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, accounts = {}, []
    for account_name in request.params.getall('accounts'):
        account = Account.by_name(account_name)
        if account is None:
            errors[account_name] = _("User account cannot be found.")
        else:
            accounts.append(account)
    if c.account not in accounts:
        accounts.append(c.account)
    if not len(errors):
        c.dataset.managers = accounts
        c.dataset.updated_at = datetime.utcnow()
        db.session.commit()
        h.flash_success(_("The team has been updated."))
    return self.team_edit(dataset, errors=errors, accounts=accounts)


@blueprint.route('/<dataset>/editor/drop', methods=['POST'])
def drop(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    dataset.updated_at = datetime.utcnow()
    dataset.drop()
    solr.drop_index(dataset.name)
    dataset.init()
    dataset.generate()
    AggregationCache(dataset).invalidate()

    # For every source in the dataset we set the status to removed
    for source in dataset.sources:
        for run in source.runs:
            run.status = Run.STATUS_REMOVED

    db.session.commit()
    flash_success(_("The dataset has been cleared."))
    return redirect(url_for('editor.index', dataset=dataset.name))


@blueprint.route('/<dataset>/editor/publish', methods=['POST'])
def publish(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    if not dataset.private:
        abort(400, _("This dataset is already public!"))
    dataset.private = False
    dataset.updated_at = datetime.utcnow()
    db.session.commit()

    # Need to invalidate the cache of the dataset index
    cache = DatasetIndexCache()
    cache.invalidate()

    public_url = url_for('dataset.view', dataset=dataset.name)
    flash_success(
        _("Congratulations, the dataset has been "
          "published. It is now available at: %s") % public_url)
    return redirect(url_for('editor.index', dataset=dataset.name))


@blueprint.route('/<dataset>/editor/retract', methods=['POST'])
def retract(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    if dataset.private:
        abort(400, _("This dataset is already private!"))
    c.dataset.private = True
    c.dataset.updated_at = datetime.utcnow()
    AggregationCache(c.dataset).invalidate()
    db.session.commit()

    # Need to invalidate the cache of the dataset index
    cache = DatasetIndexCache()
    cache.invalidate()

    h.flash_success(_("The dataset has been retracted. "
                      "It is no longer visible to others."))
    redirect(h.url_for(controller='editor', action='index',
                       dataset=c.dataset.name))


@blueprint.route('/<dataset>/editor/delete', methods=['POST'])
def delete(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    dataset.drop()
    solr.drop_index(dataset.name)
    db.session.delete(dataset)
    db.session.commit()
    flash_success(_("The dataset has been deleted."))
    return redirect(url_for('dataset.index'))
