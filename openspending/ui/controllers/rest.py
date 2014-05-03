import logging

from pylons import tmpl_context as c, url

from openspending.model.dataset import Dataset
from openspending.model import  meta as db
from openspending.ui.lib.base import BaseController
from openspending.ui.alttemplates import templating

log = logging.getLogger(__name__)


class RestController(BaseController):

    def index(self):
        dataset = db.session.query(Dataset).filter_by(private=False).first()
        entry = list(dataset.entries(limit=1)).pop()
        c.urls = [
            url(controller='dataset', action='view', dataset=dataset.name,
                format='json'),
            url(controller='entry', action='view', dataset=dataset.name,
                id=entry['id'], format='json')]

        return templating.render('home/rest.html')
