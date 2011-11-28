import logging
from celery.task import task

import openspending.command.celery

log = logging.getLogger(__name__)

@task(ignore_result=True)
def ping():
    log.info("Pong.")

@task(ignore_result=True)
def analyze_all_sources():
    from openspending.model import Source, meta as db
    for source in db.session.query(Source):
        analyze_source.delay(source.id)

@task(ignore_result=True)
def analyze_source(source_id):
    from openspending.model import Source, meta as db
    from openspending.importer.analysis import analyze_csv
    source = Source.by_id(source_id)
    if not source:
        log.error("No such source: %s", source_id)
    log.info("Analyzing: %s", source.url)
    source.analysis = analyze_csv(source.url)
    if 'error' in source.analysis:
        log.error(source.analysis.get('error'))
    else:
        log.info("Columns: %r", source.analysis.get('columns'))
    db.session.commit()

@task(ignore_result=True)
def load_source(source_id, sample=False):
    from openspending.model import Source
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
        importer.run(max_lines=1000, max_errors=1000)
    else:
        importer.run()
        index_dataset.delay(source.dataset.name)


@task(ignore_result=True)
def index_dataset(dataset_name):
    from openspending.lib.solr_util import build_index
    build_index(dataset_name)


