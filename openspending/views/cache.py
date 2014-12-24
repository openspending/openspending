from hashlib import sha1

from flask import current_app, request, Response, get_flashed_messages
from flask.ext.babel import get_locale
from flask.ext.login import current_user


class NotModified(Exception):
    pass


def handle_not_modified(exc):
    return Response(status=304)


def setup_caching():
    request._http_cache = current_app.config.get('CACHE')
    request._http_etag = None


def disable_cache():
    request._http_cache = False


def cache_response(resp):
    if not request._http_cache \
            or request.method not in ['GET', 'HEAD', 'OPTIONS'] \
            or resp.status_code > 399 \
            or resp.is_streamed:
        resp.cache_control.no_cache = True
        return resp

    resp.cache_control.max_age = 3600 * 6
    # TODO: Vary

    # resp.cache_control.must_revalidate = True
    if current_user.is_authenticated():
        resp.cache_control.private = True
    else:
        resp.cache_control.public = True
    if request._http_etag is None:
        etag_cache_keygen()
    resp.add_etag(request._http_etag)
    return resp


def generate_etag(keys):
    keys = [k + ':' + repr(v) for k, v in keys.items()]
    return sha1('|'.join(keys)).hexdigest()


def etag_cache_keygen(*keys):
    if not request._http_cache:
        return

    args = sorted(set(request.args.items()))
    # jquery where is your god now?!?
    args = filter(lambda (k, v): k != '_', args)
    args = [k + ':' + repr(v) for k, v in args]

    keys = {
        'flash': repr(sorted(get_flashed_messages())),
        'args': args,
        'user': current_user.id if current_user.is_authenticated() else None,
        'keys': sorted(map(lambda k: repr(k), keys)),
        'lang': get_locale().language
    }

    request._http_etag = generate_etag(keys)
    if request.if_none_match == request._http_etag:
        raise NotModified()
