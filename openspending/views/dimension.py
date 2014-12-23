import logging
import json

from werkzeug.exceptions import NotFound
from flask import Blueprint, render_template, request, redirect
from flask.ext.babel import gettext as _

from openspending.model.dimension import Dimension
from openspending.lib.helpers import etag_cache_keygen, url_for, get_dataset
from openspending.lib.widgets import get_widget
from openspending.lib.views import request_set_views
from openspending.lib.paramparser import DistinctFieldParamParser
from openspending.lib.hypermedia import dimension_apply_links, \
    member_apply_links, entry_apply_links
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import jsonify

PAGE_SIZE = 100

log = logging.getLogger(__name__)
blueprint = Blueprint('dimension', __name__)


def get_dimension(dataset, dimension):
    dataset = get_dataset(dataset)
    try:
        dimension = dataset[dimension]
        if not isinstance(dimension, Dimension):
            raise NotFound(_('This is not a dimension'))
        return dataset, dimension
    except KeyError:
        raise NotFound(_('This is not a dimension'))
    

def get_member(dataset, dimension_name, name):
    dataset = get_dataset(dataset)
    for dimension in dataset.compounds:
        if dimension.name == dimension_name:
            cond = dimension.alias.c.name == name
            members = list(dimension.members(cond, limit=1))
            if not len(members):
                raise NotFound(_('Sorry, there is no member named %(name)s',
                                 name=name))
            dimension = dimension
            member = members.pop()
            num_entries = dimension.num_entries(cond)
            return dataset, dimension, member, num_entries
    raise NotFound(_('Sorry, there is no dimension named %(name)',
                     name=dimension_name))


@blueprint.route('/<dataset>/dimensions')
@blueprint.route('/<dataset>/dimensions.<fmt:format>')
def index(dataset, format='html'):
    dataset = get_dataset(dataset)
    etag_cache_keygen(dataset.updated_at, format)
    if format == 'json':
        dimensions = [dimension_apply_links(dataset, d.as_dict())
                      for d in dataset.dimensions]
        return jsonify(dimensions)
    
    return render_template('dimension/index.html', dataset=dataset)


@blueprint.route('/<dataset>/<nodot:dimension>')
@blueprint.route('/<dataset>/<nodot:dimension>.<fmt:format>')
def view(dataset, dimension, format='html'):
    dataset, dimension = get_dimension(dataset, dimension)
    etag_cache_keygen(dataset.updated_at, format)

    if format == 'json':
        dimension = dimension_apply_links(dataset.name, dimension.as_dict())
        return jsonify(dimension)

    widget = get_widget('aggregate_table')
    widget_state = {'drilldowns': [dimension.name]}
    return render_template('dimension/view.html', dataset=dataset,
                           dimension=dimension, widget=widget,
                           widget_state=widget_state)


@blueprint.route('/<dataset>/<nodot:dimension>.distinct')
@blueprint.route('/<dataset>/<nodot:dimension>.distinct.<fmt:format>')
def distinct(dataset, dimension, format='json'):
    dataset, dimension = get_dimension(dataset, dimension)
    parser = DistinctFieldParamParser(dimension, request.args)
    params, errors = parser.parse()

    if errors:
        return jsonify({'errors': errors}, status=400)

    etag_cache_keygen(dataset.updated_at, format, parser.key())

    q = params.get('attribute').column_alias.ilike(params.get('q') + '%')
    offset = int((params.get('page') - 1) * params.get('pagesize'))
    members = dimension.members(q, offset=offset, limit=params.get('pagesize'))

    return jsonify({
        'results': list(members),
        'count': dimension.num_entries(q)
    })


@blueprint.route('/<dataset>/<dimension>/<nodot:name>')
@blueprint.route('/<dataset>/<dimension>/<nodot:name>.<fmt:format>')
def member(dataset, dimension, name, format="html"):
    dataset, dimension, member, num_entries = \
        get_member(dataset, dimension, name)
    member = member_apply_links(dataset, dimension, member)

    if format == 'json':
        return jsonify(member)
    elif format == 'csv':
        return write_csv(member)

    request_set_views(dataset, member, dimension=dimension.name)
    
    # If there are no views set up, then go direct to the entries
    # search page
    if request._ds_view is None:
        return redirect(url_for('dimension.entries',
                                dataset=dataset.name,
                                dimension=dimension.name,
                                name=member.get('name')))
    if 'embed' in request.args:
        return redirect(url_for('view.embed', dataset=dataset.name,
                                widget=view.vis_widget.get('name'),
                                state=json.dumps(view.vis_state)))

    return render_template('dimension/member.html', dataset=dataset,
                           dimension=dimension, member=member,
                           num_entries=num_entries)


@blueprint.route('/<dataset>/<dimension>/<name>/entries')
@blueprint.route('/<dataset>/<dimension>/<name>/entries.<fmt:format>')
def entries(dataset, dimension, name, format='html'):
    dataset, dimension, member, num_entries = \
        get_member(dataset, dimension, name)
    
    if format in ['json', 'csv']:
        return redirect(
            url_for('api.search',
                    format=format, dataset=dataset,
                    filter='%s.name:%s' % (dimension, name),
                    **dict(request.args.items())))

    request_set_views(dataset, member, dimension=dimension.name)
    
    entries = dataset.entries(
        dimension.alias.c.name == member['name'])
    entries = (entry_apply_links(dataset, e) for e in entries)
    return render_template('dimension/entries.html', dataset=dataset,
                           dimension=dimension, member=member,
                           num_entries=num_entries)

