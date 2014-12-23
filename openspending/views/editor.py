import logging
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, request
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import BadRequest
from colander import Invalid

from openspending.core import db
from openspending.model import Account, Run
from openspending.auth import require
from openspending.lib import solr_util as solr
from openspending.lib.helpers import url_for, get_dataset
from openspending.lib.helpers import disable_cache, flash_success
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

    entries_count = len(dataset)
    has_sources = dataset.sources.count() > 0
    source = dataset.sources.first()
    index_count = solr.dataset_entries(dataset.name)
    index_percentage = 0 if not entries_count else \
        int((float(index_count) / float(entries_count)) * 1000)
    return render_template('editor/index.html', dataset=dataset,
                           entries_count=entries_count,
                           has_sources=has_sources, source=source,
                           index_count=index_count,
                           index_percentage=index_percentage)


@disable_cache
@blueprint.route('/<dataset>/editor/core', methods=['GET'])
def core_edit(dataset, errors={}):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    key_currencies = sorted(
        [(r, n) for (r, (n, k)) in CURRENCIES.items() if k],
        key=lambda k_v: k_v[1])
    all_currencies = sorted(
        [(r, n) for (r, (n, k)) in CURRENCIES.items() if not k],
        key=lambda k_v1: k_v1[1])
    languages = sorted(LANGUAGES.items(), key=lambda k_v2: k_v2[1])
    territories = sorted(COUNTRIES.items(), key=lambda k_v3: k_v3[1])
    categories = sorted(CATEGORIES.items(), key=lambda k_v4: k_v4[1])

    if 'time' in dataset:
        available_times = [m['year'] for m in dataset['time'].members()]
        available_times = sorted(set(available_times), reverse=True)
    else:
        available_times = []

    errors = [(k[len('dataset.'):], v) for k, v in errors.items()]
    fill = dataset.as_dict()
    if errors:
        fill.update(dict(request.form.items()))
    return render_template('editor/core.html', dataset=dataset,
                           form_errors=dict(errors), form_fill=fill,
                           key_currencies=key_currencies,
                           all_currencies=all_currencies,
                           languages=languages,
                           territories=territories,
                           categories=categories)


@blueprint.route('/<dataset>/editor/core', methods=['POST'])
def core_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    errors = {}
    try:
        schema = dataset_schema(ValidationState(dataset.model))
        data = dict(request.form.items())
        data['territories'] = request.form.getlist('territories')
        data['languages'] = request.form.getlist('languages')
        data = schema.deserialize(data)
        dataset.label = data['label']
        dataset.currency = data['currency']
        dataset.category = data['category']
        dataset.description = data['description']
        dataset.default_time = data['default_time']
        dataset.territories = data['territories']
        dataset.languages = data['languages']
        db.session.commit()
        flash_success(_("The dataset has been updated."))
    except Invalid as i:
        errors = i.asdict()
    return core_edit(dataset.name, errors=errors)


@disable_cache
@blueprint.route('/<dataset>/editor/dimensions', methods=['GET'])
def dimensions_edit(dataset, errors={}, mapping=None,
                    saved=False):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    # TODO: really split up dimensions and mapping editor.
    source = dataset.sources.first()
    if source is None:
        return render_template('editor/dimensions_errors.html')

    mapping = mapping or dataset.data.get('mapping', {})
    if not len(mapping) and source and 'mapping' in source.analysis:
        mapping = source.analysis['mapping']

    fill = {'mapping': json.dumps(mapping, indent=2)}
    if len(dataset):
        return render_template('editor/dimensions_errors.html')

    return render_template('editor/dimensions.html', dataset=dataset,
                           form_fill=fill, errors=errors, saved=saved,
                           source=source)


@blueprint.route('/<dataset>/editor/dimensions', methods=['POST'])
def dimensions_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    if len(dataset):
        raise BadRequest(_("You cannot edit the dimensions model when "
                           "data is loaded for the dataset."))

    errors, mapping, saved = {}, None, False
    try:
        mapping = json.loads(request.params.get('mapping'))
        model = dataset.model
        model['mapping'] = mapping
        schema = mapping_schema(ValidationState(model))
        new_mapping = schema.deserialize(mapping)
        dataset.data['mapping'] = new_mapping
        dataset.drop()
        dataset._load_model()
        dataset.generate()
        db.session.commit()
        # h.flash_success(_("The mapping has been updated."))
        saved = True
    except (ValueError, TypeError, AttributeError):
        raise BadRequest(_("The mapping data could not be decoded as JSON!"))
    except Invalid as i:
        errors = i.asdict()
    return dimensions_edit(dataset.name, errors=errors,
                           mapping=mapping, saved=saved)


@disable_cache
@blueprint.route('/<dataset>/editor/templates', methods=['GET'])
def templates_edit(dataset, errors={}, values=None):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    fill = values or {'serp_title': dataset.serp_title,
                      'serp_teaser': dataset.serp_teaser}
    return render_template('editor/templates.html', dataset=dataset,
                           errors=errors, form_fill=fill)


@blueprint.route('/<dataset>/editor/templates', methods=['POST'])
def templates_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, values = {}, dict(request.form.items())
    try:
        dataset.serp_title = values.get('serp_title', None)
        dataset.serp_teaser = values.get('serp_teaser', None)
        db.session.commit()
        flash_success(_("The templates have been updated."))
    except Invalid as i:
        errors = i.asdict()
    return templates_edit(dataset.name, errors=errors, values=values)


@disable_cache
@blueprint.route('/<dataset>/editor/views', methods=['GET'])
def views_edit(dataset, errors={}, views=None,
               format='html'):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    views = views or dataset.data.get('views', [])
    fill = {'views': json.dumps(views, indent=2)}
    return render_template('editor/views.html', dataset=dataset,
                           errors=errors, form_fill=fill)


@blueprint.route('/<dataset>/editor/views', methods=['POST'])
def views_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, views = {}, json.loads(request.form.get('views'))
    try:
        schema = views_schema(ValidationState(dataset.model))
        dataset.data['views'] = schema.deserialize(views)
        db.session.commit()
        flash_success(_("The views have been updated."))
    except (ValueError, TypeError):
        raise BadRequest(_("The views could not be decoded as JSON!"))
    except Invalid as i:
        errors = i.asdict()
    return views_edit(dataset.name, errors=errors, views=views)


@disable_cache
@blueprint.route('/<dataset>/editor/team', methods=['GET'])
def team_edit(dataset, errors={}, accounts=None):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    accounts = accounts or dataset.managers
    accounts = json.dumps([a.as_dict() for a in accounts], indent=2)
    errors = errors
    return render_template('editor/team.html', dataset=dataset,
                           accounts=accounts, errors=errors)


@blueprint.route('/<dataset>/editor/team', methods=['POST'])
def team_update(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)

    errors, accounts = {}, []
    for account_name in request.form.getlist('accounts'):
        account = Account.by_name(account_name)
        if account is None:
            errors[account_name] = _("User account cannot be found.")
        else:
            accounts.append(account)
    if current_user not in accounts:
        accounts.append(current_user)

    if not len(errors):
        dataset.managers = accounts
        dataset.updated_at = datetime.utcnow()
        db.session.commit()
        flash_success(_("The team has been updated."))
    return team_edit(dataset.name, errors=errors, accounts=accounts)


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
        raise BadRequest(_("This dataset is already public!"))
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
        raise BadRequest(_("This dataset is already private!"))

    dataset.private = True
    dataset.updated_at = datetime.utcnow()
    AggregationCache(dataset).invalidate()
    db.session.commit()

    # Need to invalidate the cache of the dataset index
    cache = DatasetIndexCache()
    cache.invalidate()

    flash_success(_("The dataset has been retracted. "
                    "It is no longer visible to others."))
    return redirect(url_for('editor.index', dataset=dataset.name))


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
