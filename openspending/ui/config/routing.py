"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from paste.deploy.converters import asbool
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'], explicit=True)
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')
    # The ErrorTestController is used to test our custom error pages.
    map.connect('/_error_test/{action}', controller='error_test')

    # CUSTOM ROUTES HERE
    if not asbool(config.get('openspending.sandbox_mode', False)):
        map.sub_domains = True
        # Ignore the ``www`` sub-domain
        map.sub_domains_ignore = ['www', 'sandbox', 'staging']

        map.connect('/', controller='home', action='index_subdomain',
                    conditions={'sub_domain': True})

    map.connect('/', controller='home', action='index')

    map.connect('/getinvolved', controller='home', action='getinvolved')
    map.connect('/set-locale', controller='home', action='set_locale', conditions=dict(method=['POST']))
    map.connect('/sitemap.xml', controller='home', action='sitemap')

    map.connect('/login', controller='account', action='login')
    map.connect('/register', controller='account', action='register')
    map.connect('/settings', controller='account', action='settings')
    map.connect('/after_login', controller='account', action='after_login')
    map.connect('/after_logout', controller='account', action='after_logout')

    map.connect('/help/*path', controller='help', action='page')

    map.connect('/datasets.{format}', controller='dataset', action='index')
    map.connect('/datasets/cta', controller='dataset', action='cta')
    map.connect('/datasets/territories', controller='dataset',
            action='territories')
    map.connect('/datasets/new', controller='dataset', action='new')
    map.connect('/datasets', controller='dataset', action='create',
            conditions=dict(method=['POST']))
    map.connect('/datasets', controller='dataset', action='index')

    map.connect('/api', controller='api', action='index')
    map.connect('/api/search', controller='api', action='search')
    map.connect('/api/aggregate', controller='api', action='aggregate')
    map.connect('/api/mytax', controller='api', action='mytax')

    map.connect('/api/rest/', controller='rest', action='index')
    map.connect('/api/2/aggregate', controller='api2', action='aggregate')
    map.connect('/api/2/search', controller='api2', action='search')

    map.connect('/500', controller='error', action='render', code="500")

    map.connect('/__version__', controller='home', action='version')
    map.connect('/__ping__', controller='home', action='ping')

    map.connect('/{dataset}.{format}', controller='dataset', action='view')
    map.connect('/{dataset}', controller='dataset', action='view')
    map.connect('/{dataset}/explorer', controller='dataset', action='explorer')
    map.connect('/{dataset}/model.{format}', controller='dataset', action='model')
    map.connect('/{dataset}/model', controller='dataset', action='model')
    map.connect('/{dataset}/meta', controller='dataset', action='about')
    map.connect('/{dataset}/timeline', controller='dataset', action='timeline')

    map.connect('/{dataset}/views/new', controller='view', action='new')
    map.connect('/{dataset}/views', controller='view', action='create',
        conditions=dict(method=['POST']))
    map.connect('/{dataset}/views.{format}', controller='view', action='index')
    map.connect('/{dataset}/views', controller='view', action='index')
    map.connect('/{dataset}/views/{name}.{format}', controller='view', action='view')
    map.connect('/{dataset}/views/{name}', controller='view', action='view')
    map.connect('/{dataset}/embed', controller='view', action='embed')

    map.connect('/{dataset}/editor', controller='editor', action='index')
    map.connect('/{dataset}/editor/core', controller='editor',
            action='core_update', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/core', controller='editor', action='core_edit')
    map.connect('/{dataset}/editor/dimensions', controller='editor',
            action='dimensions_update', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/dimensions', controller='editor',
            action='dimensions_edit')
    map.connect('/{dataset}/editor/dimensions_src', controller='editor',
            action='dimensions_edit', mode='source')
    map.connect('/{dataset}/editor/views', controller='editor',
            action='views_update', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/views', controller='editor',
            action='views_edit')
    map.connect('/{dataset}/editor/publish', controller='editor',
            action='publish', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/retract', controller='editor',
            action='retract', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/drop', controller='editor',
            action='drop', conditions=dict(method=['POST']))
    map.connect('/{dataset}/editor/delete', controller='editor',
            action='delete', conditions=dict(method=['POST']))

    map.connect('/{dataset}/sources', controller='source',
            action='create', conditions=dict(method=['POST']))
    map.connect('/{dataset}/sources.{format}', controller='source',
            action='index')
    map.connect('/{dataset}/sources/new', controller='source', action='new')
    map.connect('/{dataset}/sources/{id}', controller='source', action='view')
    map.connect('/{dataset}/sources/{id}/load', controller='source',
            action='load', conditions=dict(method=['POST']))
    map.connect('/{dataset}/sources/{source}/runs/{id}',
            controller='run', action='view')
    map.connect('/{dataset}/sources/{source}/analysis.{format}',
                controller='source', action='analysis')

    map.connect('/{dataset}/entries.{format}', controller='entry', action='index_export')
    map.connect('/{dataset}/entries', controller='entry', action='index')
    map.connect('/{dataset}/entries/{id}.{format}', controller='entry', action='view')
    map.connect('/{dataset}/entries/{id}', controller='entry', action='view')
    map.connect('/{dataset}/entries/{id}/{action}', controller='entry')

    map.connect('/{dataset}/dimensions.{format}',
                controller='dimension', action='index')
    map.connect('/{dataset}/dimensions',
                controller='dimension', action='index')
    #map.connect('/{dataset}/dimensions/{dimension}.{format}',
    #            controller='dimension', action='view')
    #map.connect('/{dataset}/dimensions/{dimension}',
    #            controller='dimension', action='view')

    map.connect('/{dataset}/{dimension}.json',
                controller='dimension', action='view', format='json')
    #map.connect('/{dataset}/{dimension}.csv',
    #            controller='dimension', action='view', format='csv')
    map.connect('/{dataset}/{dimension}',
                controller='dimension', action='view')

    map.connect('/{dataset}/{dimension}/{name}.json',
                controller='dimension', action='member', format='json')
    map.connect('/{dataset}/{dimension}/{name}.csv',
                controller='dimension', action='member', format='csv')
    map.connect('/{dataset}/{dimension}/{name}',
                controller='dimension', action='member')

    map.connect('/{dataset}/{dimension}/{name}/entries.{format}',
                controller='dimension', action='entries')
    map.connect('/{dataset}/{dimension}/{name}/entries',
                controller='dimension', action='entries')

    map.redirect('/*(url)/', '/{url}', _redirect_code='301 Moved Permanently')
    return map
