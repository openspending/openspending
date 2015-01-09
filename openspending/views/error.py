from werkzeug.exceptions import HTTPException
from flask import request, render_template, Response


def handle_error(exc):
    status = 500
    title = exc.__class__.__name__
    message = unicode(exc)
    headers = {}
    if isinstance(exc, HTTPException):
        message = exc.get_description(request.environ)
        message = message.replace('<p>', '').replace('</p>', '')
        status = exc.code
        title = exc.name
        headers = exc.get_headers(request.environ)
    html = render_template('error.html', message=message,
                           title=title, status=status)
    return Response(html, status=status, headers=headers)
