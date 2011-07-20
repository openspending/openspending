from ckanclient import CkanClient, CkanApiError

openspending_group = 'openspending'
base_location = 'http://ckan.net/api'
api_key = None

_client = None

def configure(config=None):
    global openspending_group
    global base_location
    global api_key

    if not config:
        config = {}

    openspending_group = config.get('openspending.ckan_group', openspending_group)
    base_location = config.get('openspending.ckan_location', base_location)
    api_key = config.get('openspending.ckan_api_key', api_key)

def make_client():
    return CkanClient(base_location=base_location, api_key=api_key)

def get_client():
    global _client

    if _client:
        return _client
    else:
        _client = make_client()
        return _client

def openspending_packages():
    client = get_client()
    group = client.group_entity_get(openspending_group)

    return [Package(name) for name in group.get('packages')]

class ResourceError(Exception):
    pass

class AmbiguousResourceError(ResourceError):
    pass

class MissingResourceError(ResourceError):
    pass

class Package(object):
    def __init__(self, name):
        client = get_client()
        data = client.package_entity_get(name)
        self.name = data['name']
        self.data = data

    def __getitem__(self, k):
        return self.data[k]

    def __str__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.name)

    def __repr__(self):
        return '<%s "%s" at %s>' % (self.__class__.__name__, self.name, hex(id(self)))

    def get_resource(self, id):
        for r in self['resources']:
            if r['id'] == id:
                return r

        raise MissingResourceError(
            "Resource with id '%s' not found in %s"
            % (id, self)
        )

    def openspending_resource(self, hint):
        def has_hint(r):
            return r.get('openspending_hint') == hint

        with_hint = filter(has_hint, self['resources'])

        if len(with_hint) == 1:
            return with_hint[0]
        elif len(with_hint) == 0:
            return None
        else:
            raise AmbiguousResourceError(
                "%s has multiple resources with hint '%s'" % (self, hint)
            )

    def is_importable(self):
        try:
            model = self.openspending_resource('model')
            mapping = self.openspending_resource('model:mapping')
            data = self.openspending_resource('data')
        except AmbiguousResourceError:
            return False
        else:
            importable = (data and (model and not mapping) or (mapping and not model))
            return bool(importable)

    def metadata_for_resource(self, resource):
        ds = self.data.copy()

        del ds['id']

        ds['label'] = ds.pop('title')
        ds['description'] = ds.pop('notes')
        ds['source_url'] = resource.get('url')
        ds['source_description'] = resource.get('description')
        ds['source_format'] = resource.get('format')
        ds['source_id'] = resource.get('id')
        extras = ds.pop('extras', {})
        ds['currency'] = extras.get('currency', 'usd')
        ds['temporal_granularity'] = extras.get('temporal_granularity',
                                                'year').lower()

        del ds['resources']
        del ds['groups']

        ds = dict([ (k, v) for k, v in ds.iteritems() ])

        return ds

