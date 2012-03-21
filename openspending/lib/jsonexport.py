from datetime import datetime
import logging

from decorator import decorator

from pylons import request, response

from openspending.lib import json

log = logging.getLogger(__name__)


def default_json(obj):
    '''\
    Return a json representations for some custom objects.
    Used for the *default* parameter to json.dump[s](),
    see http://docs.python.org/library/json.html#json.dump

    Raises :exc:`TypeError` if it can't handle the object.
    '''
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("%r is not JSON serializable" % obj)

def write_json(entries, response, filename=None):
    response.content_type = 'application/json'
    if filename:
        response.content_disposition = 'attachment; filename=%s' % filename
    return generate_json(entries)

def generate_json(entries):
    for e in entries:
        yield to_json(e, indent=None) + '\n'

def write_browser_json(entries, stats, facets, response):
    """ Streaming support for large result sets, specific to the browser as
    the data is enveloped. """
    response.content_type = 'application/json'
    callback = None
    if 'callback' in request.params:
        response.content_type = 'text/javascript'
        callback = str(request.params['callback'])
    return generate_browser_json(entries, stats, facets, callback)

def generate_browser_json(entries, stats, facets, callback):
    yield callback + '({' if callback else '{'
    yield '"stats": %s, "facets": %s, "results": [' % (
            to_json(stats), to_json(facets))
    iter = entries.__iter__()
    has_next, first = True, True
    while has_next:
        try:
            row = iter.next()
        except StopIteration:
            has_next = False
        if has_next:
            if not first:
                yield ', '
            yield to_json(row)
        first = False
    yield ']})' if callback else ']}'

def to_json(data, indent=2):
    return json.dumps(data, default=default_json, indent=indent)

def to_jsonp(data):
    is_xhr = request.headers.get('x-requested-with', '').lower() == 'xmlhttprequest'
    indent = None if is_xhr else 2
    result = to_json(data, indent=indent)

    if 'callback' in request.params:
        response.headers['Content-Type'] = 'text/javascript'
        # The parameter is a unicode object, which we don't want (as it
        # causes Pylons to complain when we return a unicode object from
        # this function).  All reasonable values of this parameter will
        # "str" with no problem (ASCII clean).  So we do that then.
        cbname = str(request.params['callback'])
        result = '%s(%s);' % (cbname, result)
    else:
        response.headers['Content-Type'] = 'application/json'
    return result

@decorator
def jsonpify(func, *args, **kwargs):
    """\
    A decorator that reformats the output as JSON; or, if the
    *callback* parameter is specified (in the HTTP request), as JSONP.

    Modelled after pylons.decorators.jsonify.
    """
    data = func(*args, **kwargs)
    return to_jsonp(data)
