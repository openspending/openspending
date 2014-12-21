from flask import Blueprint, render_template
from flask.ext.login import current_user

from openspending.model.dataset import Dataset, DatasetTerritory
from openspending.lib.solr_util import dataset_entries


blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def index():
    datasets = Dataset.all_by_account(current_user)
    territories = DatasetTerritory.dataset_counts(datasets)
    num_entries = dataset_entries(None)
    return render_template('home/index.html', datasets=datasets,
                           territories=territories, num_entries=num_entries)

