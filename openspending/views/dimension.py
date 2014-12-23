import logging
import json

from werkzeug.exceptions import BadRequest, NotFound
from flask import Blueprint, render_template, request, redirect
from flask import Response
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from colander import SchemaNode, String, Invalid

from openspending.model.dimension import Dimension
from openspending.lib.helpers import etag_cache_keygen, url_for
from openspending.lib.widgets import get_widget
from openspending.lib.paramparser import DistinctFieldParamParser
from openspending.lib.hypermedia import dimension_apply_links, \
    member_apply_links, entry_apply_links
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_json, to_jsonp

PAGE_SIZE = 100

log = logging.getLogger(__name__)
blueprint = Blueprint('dimension', __name__)


def get_dimension(self, dataset, dimension):
    dataset = get_dataset(dataset)
    try:
        c.dimension = c.dataset[dimension]
    except KeyError:
        raise NotFound(_('This is not a dimension'))
    if not isinstance(c.dimension, Dimension):
        raise NotFound(_('This is not a dimension'))


def get_member(dataset, dimension_name, name):
    dataset = get_dataset(dataset)
    c.dimension = dimension_name
    for dimension in c.dataset.compounds:
        if dimension.name == dimension_name:
            cond = dimension.alias.c.name == name
            members = list(dimension.members(cond, limit=1))
            if not len(members):
                raise NotFound(_('Sorry, there is no member named %(name)s',
                                 name=name)
            c.dimension = dimension
            c.member = members.pop()
            c.num_entries = dimension.num_entries(cond)
            return
    raise NotFound(_('Sorry, there is no dimension named %(name)',
                     name=dimension_name))


@blueprint.route('/<dataset>/dimensions')
@blueprint.route('/<dataset>/dimensions.<format>')
def index(dataset, format='html'):
    self._get_dataset(dataset)
    etag_cache_keygen(c.dataset.updated_at, format)
    if format == 'json':
        dimensions = [dimension_apply_links(dataset, d.as_dict())
                      for d in c.dataset.dimensions]
        return to_jsonp(dimensions)
    else:
        return templating.render('dimension/index.html')


@blueprint.route('/<dataset>/dimensions/<dimension>')
@blueprint.route('/<dataset>/dimensions/<dimension>.<format>')
def view(dataset, dimension, format='html'):
    self._get_dimension(dataset, dimension)
    etag_cache_keygen(c.dataset.updated_at, format)
    if format == 'json':
        dimension = dimension_apply_links(dataset, c.dimension.as_dict())
        return to_jsonp(dimension)
    c.widget = get_widget('aggregate_table')
    c.widget_state = {'drilldowns': [c.dimension.name]}
    return templating.render('dimension/view.html')


@blueprint.route('/<dataset>/dimensions/<dimension>.distinct')
def distinct(dataset, dimension, format='json'):
    self._get_dimension(dataset, dimension)
    parser = DistinctFieldParamParser(c.dimension, request.params)
    params, errors = parser.parse()
    etag_cache_keygen(c.dataset.updated_at, format, parser.key())

    if errors:
        response.status = 400
        return {'errors': errors}

    q = params.get('attribute').column_alias.ilike(params.get('q') + '%')
    offset = int((params.get('page') - 1) * params.get('pagesize'))
    members = c.dimension.members(
        q,
        offset=offset,
        limit=params.get('pagesize'))
    return to_jsonp({
        'results': list(members),
        'count': c.dimension.num_entries(q)
    })


@blueprint.route('/<dataset>/dimensions/<dimension>/<name>')
def member(dataset, dimension, name, format="html"):
    self._get_member(dataset, dimension, name)
    handle_request(request, c, c.member, c.dimension.name)
    member = [member_apply_links(dataset, dimension, c.member)]
    if format == 'json':
        return write_json(member)
    elif format == 'csv':
        return write_csv(member)

    else:
        # If there are no views set up, then go direct to the entries
        # search page
        if view is None:
            return redirect(
                url_for(controller='dimension', action='entries',
                        dataset=c.dataset.name, dimension=dimension,
                        name=name))
        if 'embed' in request.params:
            return redirect(
                url_for('view.embed', dataset=dataset.name,
                        widget=view.vis_widget.get('name'),
                        state=json.dumps(view.vis_state)))
        return templating.render('dimension/member.html')


def entries(dataset, dimension, name, format='html'):
    self._get_member(dataset, dimension, name)
    if format in ['json', 'csv']:
        return redirect(
            url_for(controller='api/version2', action='search',
                    format=format, dataset=dataset,
                    filter='%s.name:%s' % (dimension, name),
                    **request.params))

    handle_request(request, c, c.member, c.dimension.name)
    entries = c.dataset.entries(
        c.dimension.alias.c.name == c.member['name'])
    entries = (entry_apply_links(dataset, e) for e in entries)
    return templating.render('dimension/entries.html')
