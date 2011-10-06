# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""

from pylons import config, url
from routes import url_for
from genshi.template import TextTemplate
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers.markdown import markdown as _markdown
from webhelpers.number import format_number as format_number_full
from webhelpers.pylonslib import Flash as _Flash
from webhelpers.text import truncate

from openspending import model
from openspending.lib import json
from openspending.lib.util import slugify
from openspending.ui.lib.authz import have_role
from openspending.ui.lib.jsonp import to_jsonp, to_json

def markdown(*args, **kwargs):
    return literal(_markdown(*args, **kwargs))


_flash = _Flash()


def flash_success(message):
    _flash(message, category='success')


def flash_error(message):
    _flash(message, category='error')


def flash_notice(message):
    _flash(message, category='notice')


def render_value(value):
    if isinstance(value, dict):
        return value.get('label', value.get('name', value))
    return value


def convert_search_result(result):
    entry_id = result.get('id', '')
    entry = model.Entry.c.find_one({'_id': entry_id})
    if entry is None:
        return result
    return entry


def entity_slug(entity):
    '''generate an ascii slug for an entity.

    ``entity``
        A dict-like ``entity`` object

    Returns: `str`
    '''
    slug_source = entity.get('label', '')
    if not slug_source:
        slug_source = entity.get('name', '')
    if not slug_source:
        slug_source = str(entity['_id'])
    return slugify(slug_source)


def static(url):
    static_path = config.get("openspending.static_path", "/")
    url_ = "%s%s" % (static_path, url)
    version = config.get("openspending.static_cache_version", "")
    if version:
        url_ = "%s?%s" % (url_, version)
    return url_


# TODO: moved here during openspending.model evacuation.
def render_entry_custom_html(doc, entry):
    """Render dataset ``doc``'s custom html for entry ``entry``"""
    custom_html = doc.get('entry_custom_html')
    if custom_html:
        return _render_custom_html(custom_html, 'entry', entry)
    else:
        return None

def _render_custom_html(tpl, name, obj):
    if tpl:
        tpl = TextTemplate(tpl)

        ctx = {name: obj}
        stream = tpl.generate(**ctx)
        return stream.render()
    else:
        return None

def classifier_url(dataset, classifier, **kwargs):
    return url_for(controller='classifier',
                   action='view',
                   dataset=dataset,
                   name=classifier.get('name'),
                   taxonomy=classifier.get('taxonomy'), **kwargs)

def classifier_link(classifier, **kwargs):
    kwargs['class'] = 'classifier-link'
    return link_to(classifier.get('label', classifier.get('name')),
                   classifier_url(dataset, classifier),
                   **kwargs)

def dataset_url(dataset, **kwargs):
    return url_for(controller='dataset',
                   action='view', dataset=dataset.name, **kwargs)


def dataset_link(dataset, **kwargs):
    kwargs['class'] = 'dataset-link'
    return link_to(dataset.label or dataset.name,
                   dataset_url(dataset),
                   **kwargs)


def entry_url(dataset, entry, **kwargs):
    kwargs.setdefault('action', 'view')
    return url_for(controller='entry', id=str(entry['id']),
                   dataset=dataset, **kwargs)


def entry_link(dataset, entry, **kwargs):
    kwargs['class'] = 'entry-link'
    return link_to(entry.get('label', entry.get('name', "(Unnamed)")),
                   entry_url(dataset, entry), **kwargs)

url_functions = {'classifier': classifier_url,
                 'entry': entry_url,
                 'dataset': dataset_url}

link_functions = {'classifier': classifier_link,
                  'entry': entry_link,
                  'dataset': dataset_link}


def dimension_url(obj):
    fallback = lambda o: '#'
    return _gen_dimension(obj, url_functions, fallback)


def dimension_link(obj):
    return _gen_dimension(obj, link_functions, render_value)


def _gen_dimension(obj, map, fallback):
    '''
    Function to generate links for denormalized
    classifiers, entities, datasets or entries that
    contain a DBRef.

    Takes a dict *obj* which should contain a pymongo
    :class:`bson.dbref.DBRef` object in the key 'ref'
    and calls a function in the dictionary *map* based
    on the collection the DBRef links to with the
    dereferenced mongodb document as a parameter.

    ``obj``
        A ``dict`` with the denormalized values
    ``map``
        A ``dict`` where the keys are collection names
        and the values are functions that accept the *obj*
        as a parameter.
    ``fallback``
        A function that can be used as a fallback if no
        function is found in *map*.

    Return: The return value of one of the functions in *map*
    or the retrn value of the fallback function.
    '''
    if not isinstance(obj, dict):
        return fallback(obj)
    ref = obj.get('ref', {})
    if not isinstance(ref, dict):
        ref = ref.as_doc()
    return map.get(ref.get('$ref'), fallback)(obj)


def url_from_solr_doc(solr_doc, model_type, prefix='', **kwargs):
    '''
    Helper to use the *_url() functions in this module with
    documents returned by a solr query.

    ``solr_doc``
        A document returned by solr
    ``model_type``
        A model type. type: string ('entity', 'classifier',
        'entry' or 'dataset')
    ``prefix``
        The prefix inside the solr doc. Solr docs are returned
        as flat dictionary with a '.' as a seperator. E.g.
        the dimension "from", which is a dict in mongodb,
        will be returned as "from.id", "from.name", ...
        The prefix for from is "from."
    ``**kwargs``
        Arguments that will be passed to the url function,
        e.g. action or format.
    '''
    return _gen_from_solr_doc(solr_doc, model_type, prefix,
                              url_functions, **kwargs)


def link_from_solr_doc(solr_doc, model_type, prefix='', **kwargs):
    '''
    Helper to use the *_link() functions in this module with
    documents returned by a solr query.

    ``solr_doc``
        A document returned by solr
    ``model_type``
        A model type. type: string ('entity', 'classifier',
        'entry' or 'dataset')
    ``prefix``
        The prefix inside the solr doc. Solr docs are returned
        as flat dictionary with a '.' as a seperator. E.g.
        the dimension "from", which is a dict in mongodb,
        will be returned as "from.id", "from.name", ...
        The prefix for from is "from."
    ``**kwargs``
        Arguments that will be passed to the url function,
        e.g. action or format.
    '''
    return _gen_from_solr_doc(solr_doc, model_type, prefix,
                              link_functions, **kwargs)


def _gen_from_solr_doc(solr_doc, model_type, prefix, functions, **kwargs):
    '''
    Helper to use the functions in this module with
    documents returned by a solr query.

    ``solr_doc``
        A document returned by solr
    ``model_type``
        A model type. type: string ('entity', 'classifier',
        'entry' or 'dataset')
    ``prefix``
        The prefix inside the solr doc. Solr docs are returned
        as flat dictionary with a '.' as a seperator. E.g.
        the dimension "from", which is a dict in mongodb,
        will be returned as "from.id", "from.name", ...
        The prefix for from is "from."
    ``functions``
        A ``dict`` where keys are model types and values are functions
        to call with a dict (extracted from the solr document) and the
        ***kwargs*.
    ``**kwargs``
        Arguments that will be passed to the url function,
        e.g. action or format.
    '''
    obj = {}
    attributes = (('id', '_id'),
                  ('name', 'name'),
                  ('label', 'label'))
    for (source, target) in attributes:
        obj[target] = solr_doc.get("%s%s" % (prefix, source), '')
    function = functions.get(model_type, None)
    if function is None:
        return '#'
    else:
        return function(obj, **kwargs)


def format_number(number):
    '''Format a number with m,b,k etc.

    '''
    if not number:
        return '-'
    # round to 3 significant figures
    tnumber = float('%.2e' % number)
    if abs(tnumber) > 1e9:
        return '%sb' % (tnumber / 1e9)
    elif abs(tnumber) > 1e6:
        return '%sm' % (tnumber / 1e6)
    elif abs(tnumber) > 1e3:
        return '%sk' % (tnumber / 1e3)
    else:
        return '%s' % number


def format_number_with_commas(number):
    '''Format a number with commas.

    NB: will convert to integer e.g. 2010.13 -> 2,010
    '''
    if number is None:
        return "-"
    s = str(int(number))
    groups = []
    while s and s[-1].isdigit():
        groups.append(s[-3:])
        s = s[:-3]
    return s + ','.join(reversed(groups))
