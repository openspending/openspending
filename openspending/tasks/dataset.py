from __future__ import absolute_import
from openspending.tasks.celery import celery

from celery.utils.log import get_task_logger
log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def analyze_all_sources():
    from openspending.model import meta as db
    from openspending.model.source import Source
    for source in db.session.query(Source):
        analyze_source.delay(source.id)


@celery.task(ignore_result=True)
def analyze_source(source_id):
    from openspending.model import meta as db
    from openspending.model.source import Source
    from openspending.importer.analysis import analyze_csv
    source = Source.by_id(source_id)
    if not source:
        log.error("No such source: %s", source_id)
        return
    log.info("Analyzing: %s", source.url)
    source.analysis = analyze_csv(source.url)
    if 'error' in source.analysis:
        log.error(source.analysis.get('error'))
    else:
        log.info("Columns: %r", source.analysis.get('columns'))
    db.session.commit()


@celery.task(ignore_result=True)
def load_source(source_id, sample=False):
    from openspending.model.source import Source
    from openspending.importer import CSVImporter
    source = Source.by_id(source_id)
    if not source:
        log.error("No such source: %s", source_id)

    if not source.loadable:
        log.error("Dataset has no mapping.")
        return

    source.dataset.generate()
    importer = CSVImporter(source)
    if sample:
        importer.run(dry_run=True, max_lines=1000, max_errors=1000)
    else:
        importer.run()
        index_dataset.delay(source.dataset.name)


@celery.task(ignore_result=True)
def index_dataset(dataset_name):
    from openspending.lib.solr_util import build_index
    build_index(dataset_name)
