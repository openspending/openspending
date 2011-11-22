from openspending.validation.model.common import mapping, sequence
from openspending.validation.model.common import key
from openspending.validation.model.predicates import chained, \
        reserved_name, database_name, nonempty_string
from openspending.validation.model.currency import CURRENCIES


def no_double_underscore(name):
    """ Double underscores are used for dataset bunkering in the
    application, may not occur in the dataset name. """
    if '__' in name:
        return "Double underscores are not allowed in dataset names."
    return True

def valid_currency(code):
    if code.upper() not in CURRENCIES:
        return "%s is not a valid currency code." % code
    return True

def unique_keys_are_attributes(state):
    """ Check that all members of the unique keys list are
    actually the names of attributes in the model. """
    attributes = list(state.attributes)
    def _check(value):
        if value not in attributes:
            return "Invalid attribute in unique keys: %s" % value
        return True
    return _check

def dataset_schema(state):
    schema = mapping('dataset')
    schema.add(key('name', validator=chained(
            nonempty_string,
            reserved_name,
            database_name,
            no_double_underscore
        )))
    schema.add(key('currency', validator=chained(
            valid_currency
        )))
    schema.add(key('label', validator=chained(
            nonempty_string,
        )))
    schema.add(key('description', validator=chained(
            nonempty_string,
        )))
    schema.add(sequence('unique_keys',
        key('key', validator=chained(
            unique_keys_are_attributes(state),
        )), missing=[]))
    return schema


