from bson import json_util

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from openspending.lib import json
from openspending.lib.csvexport import write_csv
from openspending.ui.lib.jsonp import to_jsonp

class RestAPIMixIn(object):

    accept_mimetypes = {
        "application/json": "json",
        "text/javascript": "json",
        "application/javascript": "json",
        "text/csv": "csv"
    }

    def index(self, format="html"):
        return self._view(format=format)

    def view(self, id=None, format="html"):
        return self._view(id=id, format=format)

    def _view(self, id=None, format="html"):
        handler = getattr(self, "_handle_%s" % request.method.lower(),
                self._handle_unknown)
        return handler(id, format)

    def _handle_put(self, id, format):
        account = c.account    # set by authentication middleware
        if account is not None:
            return self._write(id, format, account)
        else:
            abort(403, _("Invalid API-Key for PUT"))

    def _handle_get(self, id=None, format="html", result=None):
        if result is None:
            result = self._filter(request.GET, id)
        handler = self._find_handler(format, index=isinstance(result, list))
        if not handler:
            abort(404)
        return handler(result)

    def _handle_unknown(self, *args):
        abort(405, _("API supports only PUT and GET"))

    def _write(self, id, format, account):
        if not id:
            abort(400, _("API supports only modifiying existing resources"))
        representation = self._detect_write_representation(format)
        if representation != "json":
            abort(400, _("API supports only JSON for writing"))

        resource = self._get_by_id(id)

        resource = self._write_json(resource, request.body, account)

        read_repr = self._detect_read_representation(format)
        handler = self._find_handler(read_repr)
        return handler(resource)

    def _write_json(self, resource, data, account):
        try:
            data = json.loads(data, object_hook=json_util.object_hook)
        except ValueError as e:
            abort(400, str(e))
        if str(data["_id"]) != str(resource.id):
            abort(400, _("Cannot change _id attribute!"))

        resource.clear()    # PUT is NOT an incremental update
        resource.update(data)

        save_kwargs = {}
        resource.save(**save_kwargs)

        return resource

    def _detect_write_representation(self, format):
        for mimetype, mimeformat in self.accept_mimetypes.items():
            if format == mimeformat or \
                    mimetype in request.headers.get("Content-Type", ""):
                return mimeformat
        return "html"

    def _detect_read_representation(self, format):
        for mimetype, mimeformat in self.accept_mimetypes.items():
            if format == mimeformat or \
                    mimetype in request.headers.get("Accept", ""):
                return mimeformat
        return "html"

    def _find_handler(self, format, index=False):
        handler = None
        representation = self._detect_read_representation(format)
        if not index:
            handler = getattr(self, "_view_%s" % representation, None)
        else:
            handler = getattr(self, "_index_%s" % representation, None)
        return handler

    def _get_by_id(self, id):
        if id is None:
            self._object_not_found(id)

        result = self.model.get(id)

        if not result:
            self._object_not_found(id)

        return result

    def _filter(self, query, id=None):
        if id is None:
            filters = {}
            if hasattr(self.model, "default_filters"):
                for key, value in self.model.default_filters.items():
                    filters[key] = value
            if hasattr(self.model, "optional_filters"):
                for key in self.model.optional_filters:
                    if query.get(key):
                        filters[key] = query[key]
            if hasattr(self.model, "required_filters"):
                for key in self.model.required_filters:
                    if not query.get(key):
                        abort(400, ('400 Bad Request -- required filter '
                                    '%s not set' % key))
                    filters[key] = query[key]
            result = list(self.model.find(filters))
            return result
        else:
            result = self.model.get(id)
            if not result:
                self._object_not_found(id)
        return result

    def _view_csv(self, result):
        if not isinstance(result, list):
            result = [result]
        write_csv(result, response)
        return
    _index_csv = _view_csv

    def _view_json(self, result):
        return to_jsonp(result)
    _index_json = _view_json


    def _object_not_found(self, id):
        abort(404, _('Sorry, there is no %s with code %r') %
              (self.model.__name__.lower(), id))
