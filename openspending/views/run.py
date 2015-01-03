import logging

from flask import Blueprint, render_template
from flask.ext.babel import gettext as _
from werkzeug.exceptions import BadRequest

from openspending.model.source import Source
from openspending.model.run import Run
from openspending.model.log_record import LogRecord
from openspending.auth import require
from openspending.lib.helpers import get_dataset, obj_or_404, get_page
from openspending.lib.pagination import Page
from openspending.views.cache import disable_cache

log = logging.getLogger(__name__)
blueprint = Blueprint('run', __name__)


def get_run(dataset, source, id):
    dataset = get_dataset(dataset)
    require.dataset.update(dataset)
    source = obj_or_404(Source.by_id(source))
    if source.dataset != dataset:
        raise BadRequest(_("There is no source '%(source)s'", source=source))
    run = obj_or_404(Run.by_id(id))
    if run.source != source:
        raise BadRequest(_("There is no run '%(run)s'", run=id))
    return dataset, source, run


@blueprint.route('/<dataset>/sources/<source>/runs/<id>', methods=['GET'])
def view(dataset, source, id, format='html'):
    disable_cache()
    dataset, source, run = get_run(dataset, source, id)
    system = run.records.filter_by(category=LogRecord.CATEGORY_SYSTEM)
    num_system = system.count()
    system_page = Page(system.order_by(LogRecord.timestamp.asc()),
                       page=get_page('system_page'),
                       items_per_page=10)
    data = run.records.filter_by(category=LogRecord.CATEGORY_DATA)
    num_data = data.count()
    data_page = Page(data.order_by(LogRecord.timestamp.asc()),
                     page=get_page('data_page'),
                     items_per_page=20)
    return render_template('run/view.html', dataset=dataset,
                           source=source, run=run, num_system=num_system,
                           system_page=system_page, num_data=num_data,
                           data_page=data_page)
