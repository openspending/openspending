from flask import Blueprint, render_template, request, redirect, flash
from flask.ext.login import current_user
from flask.ext.babel import gettext

from openspending.i18n import set_session_locale
from openspending.model.dataset import Dataset, DatasetTerritory
from openspending.lib.solr_util import dataset_entries
from openspending.views.helpers import disable_cache


blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def index():
    datasets = Dataset.all_by_account(current_user)
    territories = DatasetTerritory.dataset_counts(datasets)
    num_entries = dataset_entries(None)
    return render_template('home/index.html', datasets=datasets,
                           territories=territories, num_entries=num_entries)


@disable_cache
@blueprint.route('/set-locale', methods=['POST'])
def set_locale():
    locale = request.args.get('locale')
    if locale is not None:
        set_session_locale(locale)
    return ''


@blueprint.route('/__version__')
def version():
    from openspending._version import __version__
    return __version__


@blueprint.route('/favicon.ico')
def favicon():
    return redirect('/static/img/favicon.ico', code=301)


@disable_cache
@blueprint.route('/__ping__')
def ping():
    from openspending.tasks.generic import ping
    ping.delay()
    flash(gettext("Sent ping!"), 'success')
    return redirect('/')
