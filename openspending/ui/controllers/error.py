import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, response, tmpl_context as c
from pylons.controllers.util import forward, abort
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from openspending.ui.lib.base import BaseController, render


class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    rendered_error_codes = ("404", "403", "400", "500")

    def document(self):
        """Render the error document - show custom template for 404"""
        resp = request.environ.get('pylons.original_response')

        # Don't do fancy error documents for JSON
        if resp.headers['Content-Type'] in ['text/javascript', 'application/json']:
            response.headers['Content-Type'] = resp.headers['Content-Type']
            return resp.body

        code = cgi.escape(request.GET.get('code', str(resp.status_int)))
        content = (literal(resp.body) or
                   cgi.escape(request.GET.get('message', '')))

        if code in self.rendered_error_codes:
            c.code = code
            message = content
            message = message.split('</h1>', 1)[-1]
            message = message.split('</body>', 1)[0]
            c.message = message.split('\n', 2)[-1]
            return render('../templates/%s.html' % code)
        else:
            page = error_document_template % \
                dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                     code=code,
                     message=content)
            return page

    def render(self, code):
        if code in self.rendered_error_codes:
            c.code = code
            c.message = code
            return render('../templates/%s.html' % code)
        abort(404)

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
