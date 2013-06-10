# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""

from pylons import config, url, tmpl_context, app_globals
from routes import url_for
from lxml import html
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
from openspending.lib.jsonexport import to_jsonp, to_json
import math
import os
import uuid
import md5

def markdown(*args, **kwargs):
    return literal(_markdown(*args, **kwargs))


def markdown_preview(text, length=150):
    if not text:
        return ''
    try:
        md = html.fromstring(unicode(markdown(text)))
        text = md.text_content()
    except:
        pass
    if length: 
        text = truncate(text, length=length, whole_word=True)
    return text.replace('\n', ' ')


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


def readable_url(url):
    if len(url) > 55:
        return url[:15] + " .. " + url[len(url) - 25:]
    return url


def site_url():
    return url_for(controller='home', action='index', qualified=True).rstrip('/')

def gravatar(email, size=None, default='mm'):
    """
    Generate a gravatar url based on a provided email. If email is none we
    spit out a default gravatar. The default gravatar is the mystery man (mm).
    """

    # Gravatar url structure
    gravatar_url = 'http://www.gravatar.com/avatar/{digest}?d={default}{query}'

    # If email is None we spit out a dummy digest
    if email is None:
        digest = '00000000000000000000000000000000'
    # else we spit out and md5 digest as required by Gravatar
    else:
        digest = md5.md5(email.strip().lower()).hexdigest()

    # Generate the Gravatar url
    url = gravatar_url.format(digest=digest,
                              default=default,
                              query='&s='+str(size) if size else '')

    # Return it
    return url

def script_root():
    c = tmpl_context
    if c.account and c.account.script_root and len(c.account.script_root.strip()):
        return c.account.script_root
    return app_globals.script_root


def static(url, obj=None):
    """
    Get the static uri based on the static_path configuration.
    """

    static_path = config.get("openspending.static_path", "/static/")

    if obj:
        # We append the lowercase object name and a forward slash
        static_path = '%s%s/' % (static_path, obj.__name__.lower())

    url_ = "%s%s" % (static_path, url)
    version = config.get("openspending.static_cache_version", "")
    if version:
        url_ = "%s?%s" % (url_, version)
    return url_

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

    # We use versioning so that the cache won't serve removed images
    version = config.get("openspending.static_cache_version", "")
    if version:
        uri_ = "%s?%s" % (url_, version)

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
        os.mkdir(object_upload_dir, 0744)
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

# TODO: moved here during openspending.model evacuation.
def render_entry_custom_html(dataset, entry):
    """Render dataset ``datasets``'s custom html for entry ``entry``"""
    if dataset.entry_custom_html:
        return _render_custom_html(dataset.entry_custom_html,
                'entry', entry)
    else:
        return None

def entry_description(entry):
    fragments = []
    if 'from' in entry and 'to' in entry:
        fragments.extend([
            entry.get('from').get('label'),
            entry.get('to').get('label')
            ])
    if isinstance(entry.get('description'), basestring):
        fragments.append(entry.get('description'))
    else:
        for k, v in entry.items():
            if k in ['from', 'to', 'taxonomy', 'html_url']:
                continue
            if isinstance(v, dict):
                fragments.append(v.get('label'))
            elif isinstance(v, basestring):
                fragments.append(v)
    description = " - ".join(fragments)
    return markdown_preview(description)


def _render_custom_html(tpl, name, obj):
    if tpl:
        tpl = TextTemplate(tpl)

        ctx = {name: obj}
        stream = tpl.generate(**ctx)
        return stream.render()
    else:
        return None


def member_url(dataset, dimension, member, **kwargs):
    return url_for(controller='dimension',
                   action='member',
                   dataset=dataset,
                   name=member.get('name'),
                   dimension=dimension,
                   **kwargs)


def dataset_url(dataset, **kwargs):
    return url_for(controller='dataset',
                   action='view', dataset=dataset.name, **kwargs)


def entry_url(dataset, entry, **kwargs):
    kwargs.setdefault('action', 'view')
    return url_for(controller='entry', id=str(entry['id']),
                   dataset=dataset, **kwargs)


def entry_link(dataset, entry, **kwargs):
    kwargs['class'] = 'entry-link'
    return link_to(entry.get('label', entry.get('name', "(Unnamed)")),
                   entry_url(dataset, entry), **kwargs)


def dimension_link(dataset, dimension, data):
    text = render_value(data)
    if isinstance(data, dict) and data['name']:
        text = link_to(text, member_url(dataset, dimension, data))
    return text


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
    if number == 'NaN':
        return "-"
    try:
        if math.isnan(number):
            return "-"
        s = str(int(number))
    except TypeError:
        msg = "Value was not numeric: %s (type: %s)" \
            % (repr(number), type(number))
        raise TypeError(msg)

    groups = []
    while s and s[-1].isdigit():
        groups.append(s[-3:])
        s = s[:-3]
    return s + ','.join(reversed(groups))


def script_tag(name):
    return '''<script type="text/javascript" src="''' + \
        '%s/%s.js' % (script_root(), name) + \
        '''"></script>'''

def style_tag(name):
    return '''<link rel="stylesheet" href="''' + \
        '%s/%s.css' % (script_root(), name) + \
        '''" />'''

def has_datatype_attr(c, key):
    return c.desc.get(key) and \
        hasattr(c.desc.get(key), 'datatype') and \
        c.desc.get(key).datatype=='url'
