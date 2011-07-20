
from openspending.model import Dimension


def create_dimension(dataset_name, key, label, description=None, **kwargs):
    kwargs.update({"dataset": dataset_name,
                   "key": key,
                   "label": label, 
                   "description": description})
    Dimension.c.update({"dataset": dataset_name, "key": key},
                       kwargs, upsert=True)


def dataset_dimensions(dataset_name, facets_only=False):
    query = {"dataset": dataset_name}
    if facets_only:
        query['facet'] = True
    return list(Dimension.find(query))

