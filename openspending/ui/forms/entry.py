import re
import colander

PLACEHOLDER = "(Empty)"

FLOAT_RE = re.compile(r"\-?\d[\d\,]*(\.[\d]*)?")
DATE_RE = re.compile(r"^\d{4}(\-\d{1,2}(\-\d{1,2})?)?$")


class StringOrPlaceholder(colander.String):

    def deserialize(self, node, cstruct):
        value = super(StringOrPlaceholder, self).deserialize(node, cstruct)
        return value or PLACEHOLDER


def make_date_validator(dimension, is_end):
    '''
    Factory for a context sensitive validator for dates.
    If the field is 'time', it must match :const:`DATE_RE`,
    unless it is the end date. Then it can be empty.
    For any other field, it can also be emtpy
    '''

    def _validator(node, value):
        msg_suffix = ('in the format "yyyy-mm-dd", "yyyy-mm" or "yyyy", '
                      'e.g. "2011-12-31".')
        if dimension != 'time':
            msg = '"%s" can be empty or a value %s' % (node.name, msg_suffix)
            if not value:
                return
        else:
            if is_end and not value:
                return
            msg = ('"time" (here "%s") has to be %s. The "end_column", if specified, '
                   'might be empty') % (value, msg_suffix)
        if DATE_RE.match(value) is None:
            raise colander.Invalid(node, msg)
    return _validator


def make_validator(fields):
    seen = []
    schema = colander.SchemaNode(colander.Mapping(unknown='ignore'))
    for field_ in fields:
        field = field_['field']
        datatype = field_['datatype']
        is_end = field_['is_end']
        dimension = field_['dimension']
        if field in seen:
            continue
        seen.append(field)
        if datatype == 'constant':
            continue
        elif datatype == 'float':
            schema.add(
                colander.SchemaNode(
                    colander.String(),
                    name=field,
                    missing="0.0",
                    validator=colander.Regex(FLOAT_RE,
                                             msg="Numeric format invalid")))
        elif datatype == 'date':
            schema.add(
                colander.SchemaNode(
                    colander.String(),
                    name=field,
                    validator=make_date_validator(dimension, is_end)))
        else:
            schema.add(colander.SchemaNode(StringOrPlaceholder(),
                                           name=field,
                                           missing=PLACEHOLDER))
    return schema
