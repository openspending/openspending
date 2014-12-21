from flask import url_for as flask_url_for
from flask import flash


def url_for(endpoint, **kwargs):
    return flask_url_for(endpoint, **kwargs)


def static_path(filename):
    return url_for('static', filename=filename)


def disable_cache(func):
    # TODO: set request variable
    return func


def flash_notice(message):
    return flash(message, 'notice')


def flash_error(message):
    return flash(message, 'error')


def flash_success(message):
    return flash(message, 'success')
