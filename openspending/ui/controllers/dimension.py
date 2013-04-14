import logging
import json

from pylons import request, tmpl_context as c, response
from pylons.controllers.util import abort, redirect
from pylons.i18n import _

from openspending import model
from openspending.ui.lib.base import BaseController, render, \
        sitemap, etag_cache_keygen
from openspending.ui.lib.base import etag_cache_keygen
from openspending.ui.lib.views import handle_request
from openspending.ui.lib import helpers as h
from openspending.ui.lib.helpers import url_for
from openspending.ui.lib.widgets import get_widget
from openspending.lib.paramparser import DistinctFieldParamParser
from openspending.ui.lib.hypermedia import dimension_apply_links, \
    member_apply_links, entry_apply_links
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_json, to_jsonp
from openspending.ui.alttemplates import templating
log = logging.getLogger(__name__)

PAGE_SIZE = 100


class DimensionController(BaseController):

    def _get_dimension(self, dataset, dimension):
        self._get_dataset(dataset)
        try:
            c.dimension = c.dataset[dimension]
        except KeyError:
            abort(404, _('This is not a dimension'))
        if not isinstance(c.dimension, model.Dimension):
            abort(404, _('This is not a dimension'))

    def _get_member(self, dataset, dimension_name, name):
        self._get_dataset(dataset)
        c.dimension = dimension_name
        for dimension in c.dataset.compounds:
            if dimension.name == dimension_name:
                cond = dimension.alias.c.name == name
                members = list(dimension.members(cond, limit=1))
                if not len(members):
                    abort(404, _('Sorry, there is no member named %r')
                            % name)
                c.dimension = dimension
                c.member = members.pop()
                c.num_entries = dimension.num_entries(cond)
                return
        abort(404, _('Sorry, there is no dimension named %r') % dimension_name)

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at, format)
        if format == 'json':
            dimensions = [dimension_apply_links(dataset, d.as_dict()) \
                for d in c.dataset.dimensions]
            return to_jsonp(dimensions)
        else:
            return templating.render('dimension/index.html')

    def view(self, dataset, dimension, format='html'):
        self._get_dimension(dataset, dimension)
        etag_cache_keygen(c.dataset.updated_at, format)
        if format == 'json':
            dimension = dimension_apply_links(dataset, c.dimension.as_dict())
            return to_jsonp(dimension)
        c.widget = get_widget('aggregate_table')
        c.widget_state = {'drilldowns': [c.dimension.name]}
        return templating.render('dimension/view.html')

    def sitemap(self, dataset, dimension):
        self._get_dimension(dataset, dimension)
        etag_cache_keygen(c.dataset.updated_at, 'xml')
        pages = []
        # TODO: Make this work for dimensions with more than 30,000 members.
        for member in c.dimension.members(limit=30000):
            pages.append({
                'loc': url_for(controller='dimension', action='member',
                    dataset=dataset, dimension=dimension, name=member.get('name'),
                    qualified=True),
                'lastmod': c.dataset.updated_at
                })
        return sitemap(pages)


    def distinct(self, dataset, dimension, format='json'):
        self._get_dimension(dataset, dimension)
        parser = DistinctFieldParamParser(c.dimension, request.params)
        params, errors = parser.parse()
        etag_cache_keygen(c.dataset.updated_at, format, parser.key())

        if errors:
            response.status = 400
            return {'errors': errors}

        q = params.get('attribute').column_alias.ilike(params.get('q') + '%')
        offset = int((params.get('page') - 1) * params.get('pagesize'))
        members = c.dimension.members(q, offset=offset, limit=params.get('pagesize'))
        return to_jsonp({
            'results': list(members),
            'count': c.dimension.num_entries(q)
            })

    def member(self, dataset, dimension, name, format="html"):
        self._get_member(dataset, dimension, name)
        handle_request(request, c, c.member, c.dimension.name)
        member = [member_apply_links(dataset, dimension, c.member)]
        if format == 'json':
            return write_json(member, response)
        elif format == 'csv':
            return write_csv(member, response)
        else:
            # If there are no views set up, then go direct to the entries
            # search page
            if c.view is None:
                return redirect(url_for(controller='dimension', action='entries',
                    dataset=c.dataset.name, dimension=dimension, name=name))
            if 'embed' in request.params:
                return redirect(url_for(controller='view',
                    action='embed', dataset=c.dataset.name,
                    widget=c.view.vis_widget.get('name'),
                    state=json.dumps(c.view.vis_state)))
            return templating.render('dimension/member.html')

    def entries(self, dataset, dimension, name, format='html'):
        self._get_member(dataset, dimension, name)
        if format in ['json', 'csv']:
            return redirect(url_for(controller='api2', action='search',
                format=format, dataset=dataset,
                filter='%s.name:%s' % (dimension, name),
                **request.params))

        handle_request(request, c, c.member, c.dimension.name)
        entries = c.dataset.entries(c.dimension.alias.c.name == c.member['name'])
        entries = (entry_apply_links(dataset, e) for e in entries)
        return templating.render('dimension/entries.html')
