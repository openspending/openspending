# -*- coding: utf-8 -*-
""" Helper functions """
import os
import uuid
from functools import update_wrapper

from flask import url_for as flask_url_for
from flask import flash, request
from werkzeug.exceptions import NotFound

from openspending.auth import require
from openspending.model import Dataset


def url_for(endpoint, **kwargs):
    kwargs['_external'] = True
    return flask_url_for(endpoint, **kwargs)


def static_path(filename):
    return url_for('static', filename=filename)


def obj_or_404(obj):
    if obj is None:
        raise NotFound()
    return obj


def get_dataset(name):
    dataset = obj_or_404(Dataset.by_name(name))
    require.dataset.read(dataset)
    return dataset


def get_page(param='page'):
    try:
        return int(request.args.get(param))
    except:
        return 1


def flash_notice(message):
    return flash(message, 'notice')


def flash_error(message):
    return flash(message, 'error')


def flash_success(message):
    return flash(message, 'success')


def join_filters(filters, append=None, remove=None):
    """
    Join filters which are used to filter Solr entries according to
    the OpenSpending convention. The conventions is that each key/value
    pair is joined with a colon : and the filters are joined with a
    pipe | so the output should be key1:value1|key2:value2

    The function allows users to append more values from a list to
    the output and remove values in a list from the output
    """

    if append is None:
        append = []

    if remove is None:
        remove = []

    # Join filter dictionary but skip pairs with key in remove
    filter_values = [u'%s:%s' % (key, value)
                     for (key, value) in filters.iteritems()
                     if key not in remove]
    # Extend the filters with pairs from append
    for (key, item) in append:
        # We expect the item to be a dictionary with a key name who's value
        # is the filter we want to add. If it isn't we try to add it as a
        # string and if that fails we just don't do anything
        try:
            filter_values.append('%s:%s' % (key, item.get('name', item)))
        except:
            pass

    # Return the joined filters
    return '|'.join(filter_values)


# def member_url(dataset, dimension, member, **kwargs):
#     return url_for(controller='dimension',
#                    action='member',
#                    dataset=dataset,
#                    name=member.get('name'),
#                    dimension=dimension,
#                    **kwargs)


# def dataset_url(dataset, **kwargs):
#     return url_for(controller='dataset',
#                    action='view', dataset=dataset.name, **kwargs)


# def entry_url(dataset, entry, **kwargs):
#     kwargs.setdefault('action', 'view')
#     return url_for(controller='entry', id=str(entry['id']),
#                    dataset=dataset, **kwargs)


# def entry_link(dataset, entry, **kwargs):
#     kwargs['class'] = 'entry-link'
#     return link_to(entry.get('label', entry.get('name', "(Unnamed)")),
#                    entry_url(dataset, entry), **kwargs)


# def dimension_link(dataset, dimension, data):
#     text = render_value(data)
#     if isinstance(data, dict) and data['name']:
#         text = link_to(text, member_url(dataset, dimension, data))
#     return text


