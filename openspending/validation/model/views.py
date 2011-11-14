from openspending.validation.model.common import mapping, sequence
from openspending.validation.model.common import key
from openspending.validation.model.predicates import chained, \
        database_name, nonempty_string

def key_is_attribute(state):
    """ Make sure that each key we cut over is actually a valid
    attribute name. """
    # TODO: include "year" and "month"?
    attributes = list(state.attributes)
    def _check(value):
        for key in value.keys():
            if key not in attributes:
                return "%s is not a valid attribute name." % key
        return True
    return _check

def dimension_or_not(state):
    """ There can either be a drilldown - which always has to be
    a valid dimension name - or no drilldown (i.e. an empty 
    string).
    """
    dimensions = list(state.dimensions)
    def _check(value):
        if value and len(value.strip()) and \
                value not in dimensions:
            return "%s is not a defined dimension, cannot " \
                "apply drilldown." % value
        return True
    return _check

def dimension_or_dataset(state):
    """ There can either be dimension on which to apply the view
    or the view applies to the whole dataset (i.e. the dimension 
    is set to 'dataset'.
    """
    dimensions = list(state.dimensions) + ['dataset']
    def _check(value):
        if value not in dimensions:
            return "%s is not a defined dimension or 'dataset', " \
                "cannot apply view." % value
        return True
    return _check

def view_schema(state):
    schema = mapping('view')
    schema.add(key('name', validator=chained(
            nonempty_string,
            database_name
        )))
    schema.add(key('label', validator=nonempty_string))
    schema.add(key('dimension', 
                   validator=dimension_or_dataset(state)))
    schema.add(key('drilldown', 
                   validator=dimension_or_not(state),
                   missing=None))
    schema.add(mapping('cuts', 
                       validator=key_is_attribute(state),
                       missing={}))
    return schema

def views_schema(state):
    return sequence('views', view_schema(state), missing=[])
