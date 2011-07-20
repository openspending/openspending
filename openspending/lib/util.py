import csv
import re
from unidecode import unidecode

def dict_intersection(o, d):
    intersect = {}
    for k, v in d.items():
        ov = o.get(k)
        if isinstance(v, dict) and isinstance(ov, dict):
            intersect[k] = dict_intersection(ov, v)
        else:
            if v == ov:
                intersect[k] = v
    return intersect


def fields_from_query(_dict):
    fields = []
    for k, v in _dict.items():
        if k.startswith('$'):
            if isinstance(v, dict):
                fields.extend(fields_from_query(v))
        else:
            fields.append(k)
    return fields


def deep_get(d, key, sep='.'):
    if d is None:
        return None
    if sep in key:
        car, rest = key.split(sep, 1)
        return deep_get(d.get(car), rest, sep=sep)
    else:
        return d.get(key)


def check_rest_suffix(name):
    '''\
    Assert that the ``name`` does not end with a string like
    '.csv', '.json'. Read the source for a list of all recogniced
    extensions.
    '''
    for sfx in ['csv', 'json', 'xml', 'rdf', 'html', 'htm', 'n3', 'nt']:
        assert not name.lower().endswith('.' + sfx), \
            "Names cannot end in .%s" % sfx


SLUG_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delimiter='-'):
    '''\
    Generate an ascii only slug from the text that can be
    used in urls or as a name.
    '''
    result = []
    for word in SLUG_RE.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delimiter.join(result))