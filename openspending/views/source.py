import logging

from flask import Blueprint, render_template, redirect, request
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import BadRequest
from colander import Invalid

from openspending.core import db
from openspending.model.source import Source
from openspending.auth import require
from openspending.lib.helpers import url_for, get_dataset, obj_or_404
from openspending.lib.helpers import disable_cache, flash_success
from openspending.lib.helpers import flash_error
from openspending.lib.jsonexport import jsonify
from openspending.tasks.dataset import analyze_source, load_source
from openspending.ui.validation.source import source_schema


log = logging.getLogger(__name__)
blueprint = Blueprint('source', __name__)


def get_source(dataset, id):
    dataset = get_dataset(dataset)
    source = obj_or_404(Source.by_id(id))
    if source.dataset != dataset:
        raise BadRequest(_("There is no source '%(id)s'", id=id))
    return dataset, source


@disable_cache
@blueprint.route('/<dataset>/sources/new', methods=['GET'])
def new(dataset, errors={}):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    params_dict = dict(request.form.items()) if errors else {}
    return render_template('source/new.html', dataset=dataset,
                           form_errors=errors, form_fill=params_dict)


@blueprint.route('/<dataset>/sources', methods=['POST'])
def create(dataset):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    try:
        data = source_schema().deserialize(request.form)
        source = Source(dataset, current_user, data['url'])
        db.session.add(source)
        db.session.commit()
        analyze_source.apply_async(args=[source.id], countdown=2)
        flash_success(_("The source has been created."))
        return redirect(url_for('editor.index', dataset=dataset.name))
    except Invalid as i:
        errors = i.asdict()
        errors = [(k[len('source.'):], v) for k, v in errors.items()]
        return new(dataset, dict(errors))


@disable_cache
@blueprint.route('/<dataset>/sources', methods=['GET'])
def index(dataset, format='json'):
    dataset = get_dataset(dataset)
    return jsonify([src.as_dict() for src in dataset.sources])


@blueprint.route('/<dataset>/sources/<id>', methods=['GET'])
def view(dataset, id):
    datset, source = get_source(dataset, id)
    return redirect(source.url)


@blueprint.route('/<dataset>/sources/<id>/load', methods=['POST'])
def load(dataset, id):
    """
    Load the dataset into the database. If a url parameter 'sample'
    is provided then its value is converted into a boolean. If the value
    equals true we only perform a sample run, else we do a full load.
    """
    datset, source = get_source(dataset, id)
    require.dataset.update(dataset)

    # If the source is already running we flash an error declaring that
    # we're already running this source
    if source.is_running:
        flash_error(_("Already running!"))

    # If the source isn't already running we try to load it (or sample it)
    else:
        try:
            sample = request.form.get('sample', 'false') == 'true'
            load_source.delay(source.id, sample)
            # Let the user know we're loading the source
            flash_success(_("Now loading..."))
        except Exception as e:
            raise BadRequest(e)

    # Send the user to the editor index page for this dataset
    return redirect(url_for('editor.index', dataset=dataset.name))


@blueprint.route('/<dataset>/sources/<id>/delete', methods=['POST'])
def delete(dataset, id):
    datset, source = get_source(dataset, id)
    require.dataset.update(dataset)

    # Delete the source if hasn't been sucessfully loaded
    # If it is successfully loaded we don't return an error
    # message because the user is then going around the normal
    # user interface
    if not source.successfully_loaded:
        db.session.delete(source)
        db.session.commit()

    return redirect(url_for('editor.index', dataset=dataset.name))


@blueprint.route('/<dataset>/sources/<id>/analysis.json', methods=['POST'])
def analysis(dataset, source, format='json'):
    datset, source = get_source(dataset, id)
    return jsonify(source.analysis)
