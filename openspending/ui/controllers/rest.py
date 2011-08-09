import logging

from pylons import tmpl_context as c, url

from openspending import model
from openspending.ui.lib.base import BaseController, render

log = logging.getLogger(__name__)


class RestController(BaseController):

    def index(self):
        dataset_ = model.dataset.find_one()
        c.urls = [
            url(controller='dataset', action='view', id=dataset_['name'],
                format='json'),
            url(controller='dataset', action='view', id=dataset_['_id'],
                format='json'),
            url(controller='entry', action='view',
                id=model.entry.find_one()['_id'], format='json')]

        return render('home/rest.html')
