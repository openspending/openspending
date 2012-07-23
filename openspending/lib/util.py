import csv
import re
from hashlib import sha1
from unidecode import unidecode

def flatten(data, sep='.'):
    out = {}
    for k, v in data.items():
        ksep = k + sep
        if isinstance(v, dict):
            for ik, iv in flatten(v, sep).items():
                out[ksep + ik] = iv
        else:
            out[k] = v
    return out

def hash_values(iterable):
    """Return a cryptographic hash of an iterable."""
    return sha1(''.join(sha1(unicode(val).encode('utf-8')).hexdigest() \
            for val in iterable)).hexdigest()

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
    for word in SLUG_RE.split(unicode(text).lower()):
        result.extend(unidecode(word).split())
    return unicode(delimiter.join(result))


def sort_by_reference(ref, sort, sort_fn=None):
    """

    Sort the iterable ``sort`` by ``sort_fn`` (if omitted, the whole object
    will be used to sort) according the order defined by the list given in
    ``ref``.

    Will raise nasty errors if ``ref`` and ``sort`` aren't 1-to-1, and doesn't
    currently perform any error-checking to ensure that they are.

    Example:

        ids = [4, 7, 1, 3]
        objs = [{'id': 1}, {'id': 7}, {'id': 4}, {'id': 3}]

        sorted = sort_list_pair(ids, objs, lambda x: x['id'])
        # => [{'id': 4}, {'id': 7}, {'id': 1}, {'id': 3}]

    """
    if sort_fn is None:
        sort_fn = lambda x: x

    ref_map = dict((r, idx) for idx, r in enumerate(ref))

    ordered = [None] * len(ref)
    for x in sort:
        key = sort_fn(x)
        if key in ref_map:
            ordered[ref_map[key]] = x

    return filter(lambda x: x is not None, ordered)
