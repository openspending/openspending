import logging

from pylons import tmpl_context as c

from openspending.model import Badge
from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib.base import BaseController
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)

class BadgeController(BaseController):

    def index(self, format='html'):
        """
        List all badges in the system. Default is to present the
        user with an html site, but the user can request a json list
        of badges.
        """
        c.badges = Badge.all()

        # If the requested format is json return a list of badges
        if format == 'json':
            return to_jsonp([b.as_dict() for b in c.badges])

        # Return html representation
        return templating.render('badge/index.html')
