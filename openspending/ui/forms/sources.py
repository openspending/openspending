
import re
import colander
from currency import CURRENCY_SYMBOLS

DATATYPE_NAMES = ['id', 'string', 'float', 'constant', 'date', 'currency']
DIMENSION_TYPES = ['classifier', 'entity', 'value']


def dataset_name(name):
    if not len(name):
        return u"Dataset name must not be empty!"
    if not re.match(r"[\w\-]*", name):
        return (u"Dataset name must only include English "
                "letters, numbers and underscores")
    return True


def currency_symbol(value):
    if value.upper() not in CURRENCY_SYMBOLS:
        error = (
            u'"%s" is not a valid currency code. It needs to be 3 '
            u'letters. See http://www.currency-iso.org/iso_index/'
            u'iso_tables/iso_tables_a1.htm for a list of valid currency '
            u'codes.') % value
        return error
    return True


class Dataset(colander.MappingSchema):
    typ = colander.Mapping(unknown='preserve')
    name = colander.SchemaNode(colander.String(),
                               validator=colander.Function(dataset_name))
    label = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
    currency = colander.SchemaNode(
        colander.String(),
        default='EUR',
        missing='EUR',
        validator=colander.Function(currency_symbol))


def dimension_name(name):
    if name in ['_id', 'classifiers', 'classifier_ids']:
        return u"Reserved dimension name: %s" % name
    if not re.match(r"\w\w*", name):
        return u"Invalid dimension name: %s" % name
    return True


def datatype_name(name):
    if name not in DATATYPE_NAMES:
        return u"Invalid data type: %s" % name
    return True


def dimension_type(t):
    if t not in DIMENSION_TYPES:
        return u"Unknown dimension type: %s" % t
    return True


def specific_type(t):
    def _check(n):
        if not t == n:
            return u"Invalid type"
        return True
    return _check


class Dimension(colander.MappingSchema):
    typ = colander.Mapping(unknown='preserve')
    label = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String(),
            missing=None)
    type = colander.SchemaNode(colander.String(),
                               validator=colander.Function(dimension_type))


class DateDimension(Dimension):
    column = colander.SchemaNode(colander.String())
    datatype = colander.SchemaNode(
        colander.String(),
        validator=colander.Function(specific_type('date')))
DateDimension.type = colander.SchemaNode(
    colander.String(),
    validator=colander.Function(specific_type('value')))


class AmountDimension(Dimension):
    column = colander.SchemaNode(colander.String())
    datatype = colander.SchemaNode(
        colander.String(),
        validator=colander.Function(specific_type('float')))
AmountDimension.type = colander.SchemaNode(
        colander.String(),
        validator=colander.Function(specific_type('value')))


class DimensionAttribute(colander.MappingSchema):
    typ = colander.Mapping(unknown='preserve')
    name = colander.SchemaNode(colander.String(),
                               validator=colander.Function(dimension_name))
    column = colander.SchemaNode(colander.String(),
                                 missing=None)
    end_column = colander.SchemaNode(colander.String(),
                                     missing=None)
    facet = colander.SchemaNode(colander.Boolean(),
                                missing=False)
    constant = colander.SchemaNode(colander.String(),
                                   missing=None)
    datatype = colander.SchemaNode(colander.String(),
                                   validator=colander.Function(dimension_name))


class Attributes(colander.SequenceSchema):
    attribute = DimensionAttribute()


class EntityDimension(Dimension):
    fields = Attributes()


class Mapping(colander.MappingSchema):
    typ = colander.Mapping(unknown='preserve')
    amount = AmountDimension()
    time = DateDimension()
    to = EntityDimension()

setattr(Mapping, 'from', EntityDimension())
