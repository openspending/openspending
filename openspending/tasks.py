from celery.utils.log import get_task_logger

from openspending.core import create_app, create_celery
from openspending.core import db
from openspending.model.source import Source
from openspending.importer.analysis import analyze_csv
from openspending.lib.solr_util import build_index
from openspending.importer import CSVImporter, BudgetDataPackageImporter
from openspending.importer.bdp import create_budget_data_package


log = get_task_logger(__name__)

flask_app = create_app()
celery = create_celery(flask_app)


@celery.task(ignore_result=True)
def analyze_all_sources():
    for source in db.session.query(Source):
        analyze_source.delay(source.id)


@celery.task(ignore_result=True)
def analyze_source(source_id):
    source = Source.by_id(source_id)
    if not source:
        return log.error("No such source: %s", source_id)
    log.info("Analyzing: %s", source.url)
    source.analysis = analyze_csv(source.url)
    if 'error' in source.analysis:
        log.error(source.analysis.get('error'))
    else:
        log.info("Columns: %r", source.analysis.get('columns'))
    db.session.commit()


@celery.task(ignore_result=True)
def analyze_budget_data_package(url, user, private):
    """
    Analyze and automatically load a budget data package
    """
    log.info("Analyzing: {0}".format(url))
    sources = create_budget_data_package(url, user, private)
    for source in sources:
        # Submit source to loading queue
        load_budgetdatapackage.delay(source.id)


@celery.task(ignore_result=True)
def load_source(source_id, sample=False):
    source = Source.by_id(source_id)
    if not source:
        return log.error("No such source: %s", source_id)

    if not source.loadable:
        return log.error("Dataset has no mapping.")

    source.dataset.generate()
    importer = CSVImporter(source)
    if sample:
        importer.run(dry_run=True, max_lines=1000, max_errors=1000)
    else:
        importer.run()
        index_dataset.delay(source.dataset.name)


@celery.task(ignore_result=True)
def load_budgetdatapackage(source_id, sample=False):
    """
    Same as the CSV importer except that it uses the BudgetDataPackage
    importer instead of the CSVImporter
    """
    source = Source.by_id(source_id)
    if not source:
        log.error("No such source: %s", source_id)

    if not source.loadable:
        log.error("Dataset has no mapping.")
        return

    source.dataset.generate()
    importer = BudgetDataPackageImporter(source)
    if sample:
        importer.run(dry_run=True, max_lines=1000, max_errors=1000)
    else:
        importer.run()
        index_dataset.delay(source.dataset.name)


@celery.task(ignore_result=True)
def index_dataset(dataset_name):
    build_index(dataset_name)


@celery.task(ignore_result=True)
def ping():
    log.info("Pong.")
