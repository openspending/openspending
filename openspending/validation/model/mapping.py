from openspending.validation.model.common import mapping, sequence
from openspending.validation.model.common import key
from openspending.validation.model.predicates import chained, \
        reserved_name, database_name, nonempty_string

DATATYPES = ['id', 'string', 'float', 'constant', 'date']

def valid_datatype(value):
    """ Check that the datatype is known and supported. """
    if not value in DATATYPES:
        return "'%s' is an unrecognized data type" % value
    return True

def specific_datatype(type_):
    """ Date dimensions and measures require data of a 
    specific type, ensure they get it. """
    def _check(value):
        if not value == type_:
            return "The data type must be '%s', not '%s'." \
                    % (type_, value)
        return True
    return _check

def name_wrap(check, name):
    """ Apply a validator to the curried name variable, not 
    any of the actual mapping data. """
    def _check(value):
        return check(name)
    return _check

def no_dimension_id_overlap(name, state):
    """ There cannot both be a dimension of name ``foo`` and 
    a dimension named ``foo_id`` because that may be used as 
    a foreign key name on the facts table. """
    def _check(value):
        invalid_name = name + '_id'
        properties = map(lambda (x,y): x, state.mapping_items)
        if invalid_name in properties:
            return "The names %s and %s_id conflict. Please " \
                    "remove %s_id or rename it." % (name, name, name)
        return True
    return _check

def require_one_key_column(mapping):
    """ At least one dimension needs to be marked as a ``key``
    to be used to generate unique entry identifiers. """
    for prop, meta in mapping.items():
        if meta.get('key') is True:
            return True
    return "At least one dimension needs to be marked as a 'key' " \
        "which can be used to uniquely identify entries in this " \
        "dataset."

def require_time_dimension(mapping):
    """ Each mapping needs to have a time dimension. """
    if 'time' not in mapping.keys():
        return "Mapping does not contain a time dimension." \
                "The dimension must exist and contain a date " \
                "to describe the entry."
    # TODO: in the future, this should check 'type':
    if mapping['time'].get('datatype') != 'date':
        return "The 'time' dimension must have the datatype " \
                "'date' as it will be converted to a date " \
                "dimension."
    return True

def require_amount_dimension(mapping):
    """ Each mapping needs to have a amount dimension. """
    if 'amount' not in mapping.keys():
        return "Mapping does not contain an amount measure." \
                "At least this measure must exist and contain " \
                "the key value of this entry."
    # TODO: in the future, this should check 'type':
    if mapping['amount'].get('datatype') != 'float':
        return "The amount must be a numeric the datatype " \
                "(i.e. 'float') to be a valid measure."
    return True

def compound_attribute_name_is_id_type(attribute):
    """ Whenever a compound dimension has a name attribute, this
    attribute must be munged, i.e. be of type 'id'. """
    if attribute.get('name') == 'name' and \
            attribute.get('datatype') != 'id':
        return "'name' attributes on dimensions must be of the " \
                "data type 'id' so they can be used in URLs"
    return True

def compound_attribute_label_is_string_type(attribute):
    """ Whenever a compound dimension has a label attribute, this
    attribute will be used in the UI and must be of type 'string'. 
    """
    if attribute.get('name') == 'label' and \
            attribute.get('datatype') != 'string':
        return "'label' attributes on dimensions must be of the " \
                "data type 'string' so they can be used in the UI."
    return True

def compound_attributes_include_name(attributes):
    """ Each compound dimension must have a 'name' attribute. """
    attributes = [a.get('name') for a in attributes]
    if not 'name' in attributes:
        return "Compound dimensions must have a 'name' attribute " \
                "that uniquely identifies them in the data. The " \
                "'name' attribute must be of data type 'id'."
    return True

def compound_attributes_include_label(attributes):
    """ Each compound dimension must have a 'label' attribute. """
    attributes = [a.get('name') for a in attributes]
    if not 'label' in attributes:
        return "Compound dimensions must have a 'label' attribute " \
                "that will be used to describe them in the " \
                "interface. The label must be a 'string'."
    return True

def property_schema(name, state):
    """ This is validation which is common to all properties,
    i.e. both dimensions and measures. """
    schema = mapping(name, validator=chained(
        name_wrap(nonempty_string, name),
        name_wrap(reserved_name, name),
        name_wrap(database_name, name),
        no_dimension_id_overlap(name, state)
        ))
    schema.add(key('label', validator=chained(
            nonempty_string,
        )))
    schema.add(key('description', validator=chained(
            nonempty_string,
        ), missing=None))
    return schema

def measure_schema(name, state):
    schema = property_schema(name, state)
    schema.add(key('column', validator=chained(
            nonempty_string,
        )))
    schema.add(key('datatype', validator=chained(
            nonempty_string,
            specific_datatype('float')
        )))
    return schema

def attribute_dimension_schema(name, state):
    schema = property_schema(name, state)
    schema.add(key('column', validator=chained(
            nonempty_string,
        )))
    schema.add(key('datatype', validator=chained(
            nonempty_string,
            valid_datatype,
        )))
    return schema

def date_schema(name, state):
    schema = property_schema(name, state)
    schema.add(key('column', validator=chained(
            nonempty_string,
        )))
    schema.add(key('datatype', validator=chained(
            nonempty_string,
            specific_datatype('date')
        )))
    return schema

def dimension_attribute_schema(state):
    schema = mapping('field', validator=chained(
            compound_attribute_name_is_id_type,
            compound_attribute_label_is_string_type
        ))
    schema.add(key('name', validator=chained(
            nonempty_string,
            reserved_name,
            database_name
        )))
    schema.add(key('column', validator=chained(
            nonempty_string,
        )))
    schema.add(key('datatype', validator=chained(
            nonempty_string,
            valid_datatype
        )))
    return schema

def compound_dimension_schema(name, state):
    schema = property_schema(name, state)
    schema.add(sequence('fields', dimension_attribute_schema(state),
        validator=chained(
            compound_attributes_include_name,
            compound_attributes_include_label
        )))
    return schema

def mapping_schema(state):
    schema = mapping('mapping', validator=chained(
        require_time_dimension,
        require_amount_dimension,
        require_one_key_column
        ))
    for name, meta in state.mapping_items:
        type_schema = {
            'measure': measure_schema,
            'value': attribute_dimension_schema,
            'attribute': attribute_dimension_schema,
            'date': date_schema,
            }.get(meta.get('type'), 
                  compound_dimension_schema)
        schema.add(type_schema(name, state))
    return schema


