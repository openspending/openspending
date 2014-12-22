# -*- coding: utf-8 -*-
""" Helper functions """
import os
import uuid

import babel.numbers
from flask.ext.babel import get_locale
from flask import url_for as flask_url_for
from flask import flash
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


def disable_cache(func):
    # TODO: set request variable
    return func


def etag_cache_keygen(*a):
    return


def flash_notice(message):
    return flash(message, 'notice')


def flash_error(message):
    return flash(message, 'error')


def flash_success(message):
    return flash(message, 'success')


def render_value(value):
    if isinstance(value, dict):
        return value.get('label', value.get('name', value))
    return value


def readable_url(url):
    if len(url) > 55:
        return url[:15] + " .. " + url[len(url) - 25:]
    return url


def upload(url, obj):
    """
    Get upload uri based on either the upload_uri configurations (set when
    an external web server serves the files).
    The upload uri is appended with a directory based on the provided object
    """

    # Create the uri from the upload_uri configuration (we need to remove the
    # rightmost '/' if it's there so we can avoid importing urljoin for such
    # as simple task), the lowercased object name and the provided url
    uri_ = '%s/%s/%s' % (config.get("openspending.upload_uri",
                                    "/files").rstrip('/'),
                         obj.__name__.lower(), url)

    return uri_


def get_object_upload_dir(obj):
    """
    Generate filesystem path of a dynamic upload directory based on object
    name. The dynamic directory is created in the static file folder and is
    assigned the lowercased name of the object.

    If for some reason it is not possible to get or create the directory,
    the method raises OSError.

    Use this method sparingly since it creates directories in the filesystem.
    """

    # We wrap important configuration value fetching in try. If any of them
    # fail we raise OSError to indicate we don't support upload directories
    # The only one likely to fail is the first one (getting pylons.paths)
    # since the static directory has a default value and the other value is
    # just a lowercased object name
    try:
        # Get public directory on filesystem
        pylons_upload = config['pylons.paths']['static_files']
        # Get upload directory as defined in config file (we default to a
        # folder called files (also default for
        upload_path = config.get('openspending.upload_directory', 'files')
        # Check to see the upload dir exists. If not we raise OSError
        upload_dir = os.path.join(pylons_upload, upload_path)
        if not os.path.isdir(upload_dir):
            raise OSError
    except:
        # Upload isn't supported if something happens when retrieving directory
        raise OSError("Upload not supported.")

    # Create the object's upload dir from upload dir and object name
    object_upload_dir = os.path.join(upload_dir, obj.__name__.lower())

    # Check if the directory exists, if so return the path
    if os.path.isdir(object_upload_dir):
        return object_upload_dir

    # Since the directory didn't exist we try to create it
    # We don't have to create any parent directories since we're either
    # creating this in the static folder or raising OSError (therefore we
    # use os.mkdir, not os.makedirs
    try:
        os.mkdir(object_upload_dir, 0o744)
    except OSError as exception:
        # Highly unlikely we end up here, but we will if there's a race
        # condition. We might also end up here if there's a regular file
        # in the static directory with the same name as the intended
        # object directory (errno.EEXIST will let us know).
        import errno
        if exception.errno != errno.EEXIST:
            raise

    # Successfully created, return it
    return object_upload_dir


def get_uuid_filename(filename):
    """
    Return a random uuid based path for a specific object.
    The method generates a filename (but keeps the same file extension)
    This reduces the likelyhood that a preexisting file might get overwritten.
    """

    # Get the hex value of a uuid4 generated value as new filename
    uuid_name = uuid.uuid4().get_hex()
    # Split out the extension and append it to the uuid name
    return ''.join([uuid_name, os.path.splitext(filename)[1]])


def format_currency(amount, dataset, locale=None):
    """ Wrapper around babel's format_currency which fetches the currency
    from the dataset. Uses the current locale to format the number. """
    try:
        if amount is None:
            return "-"
        if amount == 'NaN':
            return "-"
        locale = locale or get_locale()
        currency = 'USD'
        if dataset is not None and dataset.currency is not None:
            currency = dataset.currency
        return babel.numbers.format_currency(int(amount), currency, locale=locale)
    except:
        return amount


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


# def has_datatype_attr(c, key):
#     return c.desc.get(key) and \
#         hasattr(c.desc.get(key), 'datatype') and \
#         c.desc.get(key).datatype == 'url'
