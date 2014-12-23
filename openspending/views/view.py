import logging

from werkzeug.exceptions import BadRequest
from flask import Blueprint, render_template, request, redirect
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
import colander

from openspending.core import db
from openspending.model.view import View
from openspending import auth as can
from openspending.auth import require
from openspending.lib import json
from openspending.lib import widgets
from openspending.lib.helpers import get_dataset, obj_or_404
from openspending.lib.helpers import disable_cache, url_for
from openspending.lib.helpers import flash_success
from openspending.lib.views import request_set_views
from openspending.lib.jsonexport import jsonify

log = logging.getLogger(__name__)
blueprint = Blueprint('view', __name__)


class JSONSchemaType(colander.SchemaType):

    def serialize(self, node, appstruct):
        return json.dumps(appstruct)

    def deserialize(self, node, cstruct):
        try:
            return json.loads(cstruct)
        except Exception as exc:
            raise colander.Invalid(node, unicode(exc))


def valid_widget_name(widget):
    if widget in widgets.list_widgets():
        return True
    return _("Invalid widget type: %(widget)s", widget=widget)


class CreateView(colander.MappingSchema):
    label = colander.SchemaNode(colander.String())
    widget = colander.SchemaNode(
        colander.String(),
        validator=colander.Function(valid_widget_name))
    description = colander.SchemaNode(colander.String(),
                                      missing=None)
    state = colander.SchemaNode(JSONSchemaType())


def make_name(dataset, label):
    from openspending.lib.util import slugify
    from itertools import count
    name = name_orig = slugify(label)
    view = View.by_name(dataset, name)
    for i in count():
        if view is None:
            return name
        name = name_orig + str(i)
        view = View.by_name(dataset, name)


def get_named_view(dataset, name):
    dataset = get_dataset(dataset)
    named_view = obj_or_404(View.by_name(dataset, name))
    require.view.read(dataset, named_view)
    return dataset, named_view


@blueprint.route('/<dataset>/views', methods=['GET'])
@blueprint.route('/<dataset>/views.<fmt:format>', methods=['GET'])
def index(dataset, format='html'):
    dataset = get_dataset(dataset)

    request_set_views(dataset, dataset)
    
    views = View.all_by_dataset(dataset)
    if format == 'json':
        return jsonify([v.as_dict() for v in views])
    return render_template('view/index.html', dataset=dataset,
                           views=views)


@disable_cache
@blueprint.route('/<dataset>/views/new', methods=['GET'])
def new(dataset, errors={}):
    dataset = get_dataset(dataset)
    
    request_set_views(dataset, dataset)

    widgets_ = dict([(n, widgets.get_widget(n))
                     for n in widgets.list_widgets()])

    if 'dev_widget' in request.args and \
            request.args.get('dev_widget') not in widgets.list_widgets():
        n = request.args.get('dev_widget')
        widgets_[n] = widgets.get_widget(n, force=True)
    can_save = can.view.create(dataset)
    return render_template('view/new.html', dataset=dataset,
                           widgets=widgets_, errors=errors,
                           can_save=can_save)


@blueprint.route('/<dataset>/views', methods=['POST'])
def create(dataset):
    dataset = get_dataset(dataset)
    require.view.create(dataset)

    request_set_views(dataset, dataset)
    
    try:
        data = CreateView().deserialize(dict(request.form.items()))
        view = View()
        view.dataset = dataset
        view.account = current_user
        view.widget = data['widget']
        view.state = data['state']
        view.name = make_name(dataset, data['label'])
        view.label = data['label']
        view.description = data['description']
        view.public = True
        db.session.add(view)
        db.session.commit()
        return redirect(url_for('view.view', dataset=dataset.name,
                                name=view.name))
    except colander.Invalid as inv:
        return new(dataset.name, errors=inv.asdict())


@blueprint.route('/<dataset>/views/<nodot:name>', methods=['GET'])
@blueprint.route('/<dataset>/views/<nodot:name>.<fmt:format>', methods=['GET'])
def view(dataset, name, format='html'):
    dataset, named_view = get_named_view(dataset, name)
    
    request_set_views(dataset, dataset)
    
    widget = widgets.get_widget(named_view.widget)
    if format == 'json':
        return jsonify(named_view.as_dict())
    
    return render_template('view/view.html', dataset=dataset,
                           named_view=named_view, widget=widget)


@blueprint.route('/<dataset>/views/<name>', methods=['POST'])
def update(dataset, name):
    """ Update dataset. Does nothing at the moment. """
    dataset, view = get_named_view(dataset, name)
    
    # User must be allowed to update the named view
    require.view.update(dataset, view)

    # Possible update values
    # We don't update the view's name because it might have been embedded
    view.label = request.form.get('label', view.label)
    view.description = request.form.get('description', view.description)

    try:
        # Try to load the state
        view.state = json.loads(request.form['state'])
    except:
        pass

    db.session.commit()
    return redirect(url_for('view.view', dataset=dataset.name,
                            name=view.name))


@blueprint.route('/<dataset>/views/<name>', methods=['DELETE'])
def delete(dataset, name):
    dataset, named_view = get_named_view(dataset, name)
    require.view.delete(dataset, named_view)
    flash_success(_("'%(name)s' has been deleted.", name=named_view.label))
    db.session.delete(named_view)
    db.session.commit()
    return redirect(url_for('view.index', dataset=dataset.name))


@blueprint.route('/<dataset>/embed', methods=['GET'])
def embed(dataset):
    dataset = get_dataset(dataset)
    
    print request.args
    widget = request.args.get('widget')
    if widget is None:
        raise BadRequest(_("No widget type has been specified."))
    try:
        widget = widgets.get_widget(widget)
        state = json.loads(request.args.get('state', '{}'))
    except ValueError as ve:
        raise BadRequest(unicode(ve))
    return render_template('view/embed.html', dataset=dataset,
                           widget=widget, state=state)
