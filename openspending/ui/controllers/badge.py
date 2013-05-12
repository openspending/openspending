import logging
import os
from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from openspending.model import Badge, meta as db
from openspending.ui.lib.base import require
from openspending.lib.jsonexport import to_jsonp
from openspending.ui.lib import helpers as h
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

    def information(self, id, format='html'):
        """
        Show information about the badge. Default is to present the
        user with the badge on an html site, but the user can request a
        json representation of the badge
        """

        # Get the badge
        c.badge = Badge.by_id(id=id)

        # Return a json representation if the format requested is 'json'
        if format == 'json':
            return to_jsonp(c.badge.as_dict())
        
        # Return html representation
        return templating.render('badge/information.html')

    def create(self):
        """
        Create a new badge in the system
        """
        # Check if user is allowed to create a badge
        require.badge.create()

        import shutil

        name = request.params['badge-name']
        description = request.params['badge-description']
        image = request.POST['badge-image']

        try:
            # Get upload directory for Badge and generate a random filename
            upload_dir = h.get_object_upload_dir(Badge)
            random_filename = h.get_uuid_filename(image.filename)
            
            # Open the filename and copy the uploaded image
            permanent_filename = os.path.join(upload_dir, random_filename)
            permanent_image = open(permanent_filename, 'w')
            shutil.copyfileobj(image.file, permanent_image)

            static_image_path = h.static(random_filename, Badge)
            # Close image files
            image.file.close()
            permanent_image.close()
        except OSError:
            static_image_path = ''
            h.flash_error(_('Uploading files not supported at the moment.'))

        badge = Badge(name, static_image_path, description, c.account)
        db.session.add(badge)
        db.session.commit()

        redirect(h.url_for(controller='badge', action='information', 
                           id=badge.id))
