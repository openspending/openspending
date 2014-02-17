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

def expand_facets(facets, dataset):
    """
    For the given dataset we return the facets as a dict with facet
    names for keys and the value is the list of its members along with
    the total count (facet_values).
    """

    # We'll fill in and return this dict
    expanded_facets = {}

    # Find dimension names in the dataset
    dimension_names = [d.name for d in dataset.dimensions]

    # Loop over all facets (their names)
    for (facet_name, facet_members) in facets.iteritems():
        # We only act on facets which are compound dimensions
        if facet_name in dimension_names and dataset[facet_name].is_compound:
            # Get the dimension from the dataset
            dimension = dataset[facet_name]
            # We get the member names and their facet values into
            # their own variables because we need to work more with
            # the member names
            member_names = []
            facet_values = []
            for member in facet_members:
                # We've processed the members so that they're tuples
                # that look like: (name,count)
                member_names.append(member[0])
                facet_values.append(member[1])

            # Get all the members for this dimension
            members = dimension.members(dimension.alias.c.name.\
                                            in_(member_names))
            # We need to sort them by the member names so that they retain
            # the same order as the facet_alues
            members = sort_by_reference(member_names, members,
                                        lambda x: x['name'])

            # Now we zip them all up into tuples and add into the output dict
            expanded_facets[facet_name] = zip(members, facet_values)
        else:
            # If the facet isn't a compound dimension we still want to keep
            # it around
            expanded_facets[facet_name] = facet_members

    # ... and return it
    return expanded_facets
