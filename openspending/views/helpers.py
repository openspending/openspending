from flask import url_for as flask_url_for


def url_for(endpoint, **kwargs):
    return flask_url_for(endpoint, **kwargs)


def static_path(filename):
    return url_for('static', filename=filename)
