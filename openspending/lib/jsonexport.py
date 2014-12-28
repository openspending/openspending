import logging
from datetime import datetime, date
from json import JSONEncoder
from decorator import decorator

from flask import request, Response

log = logging.getLogger(__name__)


class AppEncoder(JSONEncoder):
    """ This encoder will serialize all entities that have a to_dict
    method by calling that method and serializing the result. """

    def default(self, obj):
        if hasattr(obj, 'as_dict'):
            return obj.as_dict()
        elif isinstance(obj, datetime):
            return obj.isoformat() + 'Z'
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, set):
            return [o for o in obj]
        return super(AppEncoder, self).default(obj)


def to_json(obj, encoder=None):
    if encoder is None:
        encoder = AppEncoder
    return encoder().encode(obj)


def write_json(entries, filename=None):
    headers = {'Content-Type': 'application/json'}
    if filename:
        headers['Content-Disposition'] = 'attachment; filename=%s' % filename
    return Response(generate_json(entries), headers=headers)


def generate_json(entries):
    for e in entries:
        yield to_json(e) + '\n'


def write_browser_json(entries, stats, facets):
    """ Streaming support for large result sets, specific to the browser as
    the data is enveloped. """
    mime_type = 'application/json'
    callback = None
    if 'callback' in request.args:
        mime_type = 'text/javascript'
        callback = str(request.args['callback'])
    gen = generate_browser_json(entries, stats, facets, callback)
    return Response(gen, mime_type=mime_type)


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


def jsonify(obj, status=200, headers=None, index=False, encoder=AppEncoder):
    """ Custom JSONificaton to support obj.as_dict protocol. """
    data = to_json(obj, encoder=encoder)
    if 'callback' in request.args:
        cb = request.args.get('callback')
        data = '%s && %s(%s)' % (cb, cb, data)
    return Response(data, headers=headers,
                    status=status,
                    mimetype='application/json')
