import logging

from flask import Blueprint, render_template, redirect, request
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import BadRequest

from openspending.lib.views import request_set_views
from openspending.lib.hypermedia import entry_apply_links
from openspending.lib.browser import Browser
from openspending.lib.helpers import url_for, get_dataset
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import jsonify
from openspending.lib.pagination import Page
from openspending.lib.paramparser import EntryIndexParamParser

from solr import SolrException

log = logging.getLogger(__name__)
blueprint = Blueprint('entry', __name__)


@blueprint.route('/<dataset>/entries')
@blueprint.route('/<dataset>/entries.<format>')
def index(dataset, format='html'):
    dataset = get_dataset(dataset)

    # If the format is either json or csv we direct the user to the search
    # API instead
    if format in ['json', 'csv']:
        return redirect(url_for('api.search', format=format, dataset=dataset,
                                **dict(request.args.items())))

    # Get the default view
    request_set_views(dataset, dataset)

    # Parse the parameters using the SearchParamParser (used by the API)
    parser = EntryIndexParamParser(request.args)
    params, errors = parser.parse()

    # We have to remove page from the parameters because that's also
    # used in the Solr browser (which fetches the queries)
    params.pop('page')

    # We limit ourselve to only our dataset
    params['filter']['dataset'] = [dataset.name]
    facet_dimensions = {field.name: field
                        for field in dataset.dimensions
                        if field.facet}
    params['facet_field'] = facet_dimensions.keys()

    # Create a Solr browser and execute it
    b = Browser(**params)
    try:
        b.execute()
    except SolrException as e:
        return {'errors': [unicode(e)]}

    # Get the entries, each item is a tuple of (dataset, entry)
    solr_entries = b.get_entries()
    # We are only interested in the entry in the tuple since  we know
    # the dataset
    entries = [entry[1] for entry in solr_entries]

    tmpl_context = {
        'dataset': dataset,
        'facets': b.get_expanded_facets(dataset),
        'entries': Page(entries, **dict(request.args.items())),
        'search': params.get('q', ''),
        'filters': params['filter'],
        'facet_dimensions': facet_dimensions,
        'dimensions': [dimension.name for dimension in dataset.dimensions]
    }

    if 'dataset' in tmpl_context['filters']:
        del tmpl_context['filters']['dataset']
    return render_template('entry/index.html')


@blueprint.route('/<dataset>/entries')
@blueprint.route('/<dataset>/entries.<format>')
def view(dataset, id, format='html'):
    """
    Get a specific entry in the dataset, identified by the id. Entry
    can be return as html (default), json or csv.
    """
    dataset = get_dataset(dataset)

    # Get the entry that matches the given id. dataset.entries is
    # a generator so we create a list from it's responses based on the
    # given constraint
    entries = list(dataset.entries(dataset.alias.c.id == id))
    # Since we're trying to get a single entry the list should only
    # contain one entry, if not then we return an error
    if not len(entries) == 1:
        raise BadRequest(_('Sorry, there is no entry %(id)s', id=id))

    # Add urls to the dataset and assign assign it as a context variable
    entry = entry_apply_links(dataset, entries.pop())

    # Get the amount for the entry
    amount = entry.get('amount')
    # We adjust for inflation if the user as asked for this to be inflated
    if 'inflate' in request.params:
        try:
            # Inflate the amount. Target date is provided in request.params
            # as value for inflate and reference date is the date of the
            # entry. We also provide a list of the territories to extract
            # a single country for which to do the inflation
            c.inflation = h.inflate(amount, request.params['inflate'],
                                    c.time, c.dataset.territories)

            # The amount to show should be the inflated amount
            # and overwrite the entry's amount as well
            c.amount = c.inflation['inflated']
            c.entry['amount'] = c.inflation['inflated']

            # We include the inflation response in the entry's dict
            # HTML description assumes every dict value for the entry
            # includes a label so we include a default "Inflation
            # adjustment" for it to work.
            c.inflation['label'] = 'Inflation adjustment'
            c.entry['inflation_adjustment'] = c.inflation
        except:
            # If anything goes wrong in the try clause (and there's a lot
            # that can go wrong). We just say that we can't adjust for
            # inflation and set the context amount as the original amount
            h.flash_notice(_('Unable to adjust for inflation'))
            c.amount = amount
    else:
        # If we haven't been asked to inflate then we just use the
        # original amount
        c.amount = amount

    # Add custom html for the dataset entry if the dataset has some
    # custom html
    # 2013-11-17 disabled this as part of removal of genshi as depended on
    # a genshi specific helper.
    # TODO: reinstate if important
    # c.custom_html = h.render_entry_custom_html(c.dataset, c.entry)

    # Add the rest of the dimensions relating to this entry into a
    # extras dictionary. We first need to exclude all dimensions that
    # are already shown and then we can loop through the dimensions
    excluded_keys = ('time', 'amount', 'currency', 'from',
                     'to', 'dataset', 'id', 'name', 'description')

    c.extras = {}
    if dataset:
        # Create a dictionary of the dataset dimensions
        c.desc = dict([(d.name, d) for d in dataset.dimensions])
        # Loop through dimensions of the entry
        for key in entry:
            # Entry dimension must be a dataset dimension and not in
            # the predefined excluded keys
            if key in c.desc and \
                    key not in excluded_keys:
                c.extras[key] = c.entry[key]

    # Return entry based on
    if format == 'json':
        return jsonify(entry)
    elif format == 'csv':
        return write_csv([entry])
    else:
        return render_template('entry/view.html')


@blueprint.route('/search')
def search():
    return render_template('entry/search.html')
