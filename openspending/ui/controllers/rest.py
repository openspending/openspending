import logging

from pylons import tmpl_context as c, url

from openspending.model import Dataset, meta as db
from openspending.ui.lib.base import BaseController, render

log = logging.getLogger(__name__)


class RestController(BaseController):

    def index(self):
        dataset = db.session.query(Dataset).first()
        entry = list(dataset.materialize(limit=1)).pop()
        c.urls = [
            url(controller='dataset', action='view', name=dataset.name,
                format='json'),
            url(controller='entry', action='view', dataset=dataset.name,
                id=entry['id'], format='json')]

        return render('home/rest.html')
