import logging
import os
import random
import subprocess

from pylons import request, response, tmpl_context as c
from pylons import app_globals, url, config
from pylons.controllers.util import redirect, abort
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from openspending.ui.i18n import set_session_locale
from openspending.ui.lib import views
from openspending.ui.lib.base import BaseController, render, require
from openspending.ui.lib.helpers import flash_success, flash_error
from openspending.ui.lib.content import ContentResource

log = logging.getLogger(__name__)

class ContentController(BaseController):

    def view(self, section, path):
        c.resource = ContentResource(section, path)
        c.content_section = section
        if not c.resource.exists():
            abort(404, _("Sorry, the selected resource could not be found"))
        if not c.resource.is_html():
            redirect(c.resource.url)
        return render('content/view.html')
