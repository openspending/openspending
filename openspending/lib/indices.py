import logging

from sqlalchemy.sql.expression import select, func
from sqlalchemy.orm import aliased

from openspending.core import db
from openspending.lib.helpers import url_for
from openspending.model.dataset import (Dataset, DatasetLanguage,
                                        DatasetTerritory)
from openspending.reference.country import COUNTRIES
from openspending.reference.category import CATEGORIES
from openspending.reference.language import LANGUAGES


log = logging.getLogger(__name__)


def language_index(datasets):
    """ Get a list of languages by count of datasets """
    # Get a list of languages in the current list of datasets
    languages = DatasetLanguage.dataset_counts(datasets)
    # Return a list of languages as dicts with code, count, url and label
    return [{'code': code, 'count': count,
             'url': url_for('dataset.index', languages=code),
             'label': LANGUAGES.get(code, code)}
            for (code, count) in languages]


def territory_index(datasets):
    """ Get a list of territories by count of datasets """
    # Get a list of territories in the current list of datasets
    territories = DatasetTerritory.dataset_counts(datasets)
    # Return a list of territories as dicts with code, count, url and label
    return [{'code': code, 'count': count,
             'url': url_for('dataset.index', territories=code),
             'label': COUNTRIES.get(code, code)}
            for (code, count) in territories]


def category_index(datasets):
    """ Get a list of categories by count of datasets """
    # Get the dataset ids in the current list of datasets
    ds_ids = [d.id for d in datasets]
    if len(ds_ids):
        # If we have dataset ids we count the dataset by category
        q = select([Dataset.category, func.count(Dataset.id)],
                   Dataset.id.in_(ds_ids), group_by=Dataset.category,
                   order_by=func.count(Dataset.id).desc())

        # Execute the queery to the the list of categories
        categories = db.session.bind.execute(q).fetchall()
        # Return a list of categories as dicts with category, count, url
        # and label
        return [{'category': category, 'count': count,
                 'url': url_for('dataset.index', category=category),
                 'label': CATEGORIES.get(category, category)}
                for (category, count) in categories if category is not None]

    # We return an empty string if no datasets found
    return []


def dataset_index(account, languages=[], territories=[], category=None):
    # Get all of the public datasets ordered by when they were last updated
    results = Dataset.all_by_account(account, order=False)
    results = results.order_by(Dataset.updated_at.desc())

    # Filter by languages if they have been provided
    for language in languages:
        l = aliased(DatasetLanguage)
        results = results.join(l, Dataset._languages)
        results = results.filter(l.code == language)

    # Filter by territories if they have been provided
    for territory in territories:
        t = aliased(DatasetTerritory)
        results = results.join(t, Dataset._territories)
        results = results.filter(t.code == territory)

    # Filter category if that has been provided
    if category:
        results = results.filter(Dataset.category == category)

    return list(results)
