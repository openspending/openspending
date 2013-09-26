import logging
import datetime

from pylons import app_globals, request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.i18n import _

from openspending.ui.lib.base import BaseController, render, \
        sitemap, etag_cache_keygen
from openspending.ui.lib.views import handle_request
from openspending.ui.lib.hypermedia import entry_apply_links
from openspending.lib.csvexport import write_csv
from openspending.lib.jsonexport import write_json, to_jsonp
from openspending.ui.lib import helpers as h
from openspending.reference import country
from openspending.ui.alttemplates import templating
from openspending.reference import country

log = logging.getLogger(__name__)


class EntryController(BaseController):

    def index(self, dataset, format='html'):
        self._get_dataset(dataset)

        if format in ['json', 'csv']:
            return redirect(h.url_for(controller='api2', action='search',
                format=format, dataset=dataset,
                **request.params))

        handle_request(request, c, c.dataset)
        return templating.render('entry/index.html')

    def view(self, dataset, id, format='html'):
        """
        Get a specific entry in the dataset, identified by the id. Entry
        can be return as html (default), json or csv.
        """

        # Generate the dataset
        self._get_dataset(dataset)
        # Get the entry that matches the given id. c.dataset.entries is 
        # a generator so we create a list from it's responses based on the
        # given constraint
        entries = list(c.dataset.entries(c.dataset.alias.c.id == id))
        # Since we're trying to get a single entry the list should only 
        # contain one entry, if not then we return an error
        if not len(entries) == 1:
            abort(404, _('Sorry, there is no entry %r') % id)
        # Add urls to the dataset and assign assign it as a context variable
        c.entry = entry_apply_links(dataset, entries.pop())

        # Get and set some context variables from the entry
        # This shouldn't really be necessary but it's here so nothing gets
        # broken
        c.id = c.entry.get('id')
        c.from_ = c.entry.get('from')
        c.to = c.entry.get('to')
        c.currency = c.entry.get('currency', c.dataset.currency).upper()
        c.time = c.entry.get('time')

        # Get the amount for the entry
        amount = c.entry.get('amount')
        # We adjust for inflation if the user as asked for this to be inflated
        if request.params.has_key('inflate'):
            # Get the year for this time entry which will serve as
            # reference year. We use years since that's what the inflation
            # data offers
            reference = datetime.date(int(c.time['year']),1,1)
            try:
                # Get the target year from the inflate request parameter. Again
                # we use years but users should still be able to put in dates
                # so that we might later support months or dates.
                target = datetime.date(int(request.params['inflate'][:4]),1,1)

                # Get the country we inflate for. This again is imprecise since
                # there might be more than one countries tied to a dataset, for
                # now we just get the first one. We uppercase it as well to
                # help the inflation method
                dataset_country = country.COUNTRIES.get(
                    c.dataset.territories[0])

                # Do the inflation via a helper function and set the context
                # amount as the inflated amount
                c.amount = h.inflate(amount, target, reference, dataset_country)
                
                # Set a context variable to make the inflation parameters
                # available to the templates
                c.inflation = {'reference': reference, 'target': target,
                               'original': amount,
                               'label':'Inflation adjustment'}

                # Need to overwrite amount and set inflation parameters
                # in c.entry for json and csv responses
                c.entry['amount'] = c.amount
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
        c.custom_html = h.render_entry_custom_html(c.dataset,
                                                   c.entry)

        # Add the rest of the dimensions relating to this entry into a
        # extras dictionary. We first need to exclude all dimensions that
        # are already shown and then we can loop through the dimensions
        excluded_keys = ('time', 'amount', 'currency', 'from',
                         'to', 'dataset', 'id', 'name', 'description')

        c.extras = {}
        if c.dataset:
            # Create a dictionary of the dataset dimensions
            c.desc = dict([(d.name, d) for d in c.dataset.dimensions])
            # Loop through dimensions of the entry
            for key in c.entry:
                # Entry dimension must be a dataset dimension and not in
                # the predefined excluded keys
                if key in c.desc and \
                        not key in excluded_keys:
                    c.extras[key] = c.entry[key]

        # Return entry based on 
        if format == 'json':
            return to_jsonp(c.entry)
        elif format == 'csv':
            return write_csv([c.entry], response)
        else:
            return templating.render('entry/view.html')

    def search(self):
        c.content_section = 'search'
        return templating.render('entry/search.html')

    def sitemap(self, dataset, page):
        self._get_dataset(dataset)
        etag_cache_keygen(c.dataset.updated_at, 'xml')
        limit = 30000
        pages = []
        for entry in c.dataset.entries(limit=limit,
                                       offset=(int(page) - 1) * limit,
                                       step=limit, fields=[]):
            pages.append({
                'loc': h.url_for(controller='entry', action='view',
                                 dataset=dataset, id=entry.get('id'),
                                 qualified=True),
                'lastmod': c.dataset.updated_at
                })
        return sitemap(pages)
