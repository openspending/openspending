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


def script_root():
    c = tmpl_context
    if c.account and c.account.script_root and len(c.account.script_root.strip()):
        return c.account.script_root
    return app_globals.script_root


def static(url):
    static_path = config.get("openspending.static_path", "/static/")
    url_ = "%s%s" % (static_path, url)
    version = config.get("openspending.static_cache_version", "")
    if version:
        url_ = "%s?%s" % (url_, version)
    return url_


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
