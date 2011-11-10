import csv
import re
from hashlib import sha1
from unidecode import unidecode

def flatten(data, sep='.'):
    out = {}
    for k, v in data.items():
        if isinstance(v, dict):
            for ik, iv in flatten(v, sep).items():
                out[k + sep + ik] = iv
        else:
            out[k] = v
    return out

def hash_values(iterable):
    """Return a cryptographic hash of an iterable."""
    return sha1(''.join(sha1(unicode(val)).hexdigest() for val in iterable)).hexdigest()

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

