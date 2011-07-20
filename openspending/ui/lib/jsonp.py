from datetime import datetime
import logging

from bson.dbref import DBRef
from bson.objectid import ObjectId

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
    if isinstance(obj, DBRef):
        return obj.as_doc()
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("%r is not JSON serializable" % obj)


def to_json(data):
    return json.dumps(data, default=default_json, indent=2)


def to_jsonp(data):
    result = to_json(data)
    if 'callback' in request.params:
        response.headers['Content-Type'] = 'text/javascript'
        log.debug("Returning JSONP wrapped action output")
        # The parameter is a unicode object, which we don't want (as it
        # causes Pylons to complain when we return a unicode object from
        # this function).  All reasonable values of this parameter will
        # "str" with no problem (ASCII clean).  So we do that then.
        cbname = str(request.params['callback'])
        result = '%s(%s);' % (cbname, result)
    else:
        response.headers['Content-Type'] = 'application/json'
        log.debug("Returning JSON wrapped action output")
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
