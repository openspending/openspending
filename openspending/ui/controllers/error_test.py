"""
ErrorTestController is used solely in functional testing of the custom error
documents.
"""
from openspending.etl.ui.lib.base import BaseController, abort

class ErrorTestController(BaseController):
    def not_found(self):
        abort(404, "Custom 404 error message")

    def not_authorised(self):
        abort(403, "Custom 403 error message")

    def server_error(self):
        abort(500, "Custom 500 error message")

