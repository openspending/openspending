"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper


def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'], explicit=True)
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved

    # CUSTOM ROUTES HERE
    
    map.connect('/badges', controller='badge', action='index')
    map.connect('/badges.{format}', controller='badge', action='index')
    map.connect('/badges/create', controller='badge', action='create',
                conditions=dict(method=['POST']))
    map.connect(
        '/badge/{id}.{format}',
        controller='badge',
        action='information')
    map.connect('/badge/{id}', controller='badge', action='information')

    map.connect('/search', controller='entry', action='search')

    map.connect(
        '/api/2/aggregate',
        controller='api/version2',
        action='aggregate')
    map.connect('/api/2/search', controller='api/version2', action='search')
    map.connect(
        '/api/2/new',
        controller='api/version2',
        action='create',
        conditions=dict(
            method=['POST']))
    map.connect(
        '/api/2/permissions',
        controller='api/version2',
        action='permissions')

    map.connect('/{dataset}.{format}', controller='dataset', action='view')
    map.connect('/{dataset}', controller='dataset', action='view')
    map.connect('/{dataset}/explorer', controller='dataset', action='explorer')
    map.connect(
        '/{dataset}/model.{format}',
        controller='dataset',
        action='model')
    map.connect('/{dataset}/model', controller='dataset', action='model')
    map.connect('/{dataset}/meta', controller='dataset', action='about')
    map.connect('/{dataset}/timeline', controller='dataset', action='timeline')

    map.connect('/{dataset}/views/new', controller='view', action='new')
    map.connect('/{dataset}/views', controller='view', action='create',
                conditions=dict(method=['POST']))
    map.connect('/{dataset}/views.{format}', controller='view', action='index')
    map.connect('/{dataset}/views', controller='view', action='index')
    map.connect(
        '/{dataset}/views/{name}.{format}',
        controller='view',
        action='view')
    map.connect('/{dataset}/views/{name}', controller='view', action='update',
                conditions=dict(method=['POST']))
    map.connect('/{dataset}/views/{name}', controller='view', action='delete',
                conditions=dict(method=['DELETE']))
    map.connect('/{dataset}/views/{name}', controller='view', action='view')
    map.connect('/{dataset}/embed', controller='view', action='embed')

    map.connect(
        '/{dataset}/entries.{format}',
        controller='entry',
        action='index')
    map.connect('/{dataset}/entries', controller='entry', action='index')
    map.connect(
        '/{dataset}/entries/{id}.{format}',
        controller='entry',
        action='view')
    map.connect('/{dataset}/entries/{id}', controller='entry', action='view')
    map.connect('/{dataset}/entries/{id}/{action}', controller='entry')

    map.connect('/{dataset}/give', controller='badge', action='give',
                conditions=dict(method=['POST']))

    map.connect('/{dataset}/dimensions.{format}',
                controller='dimension', action='index')
    map.connect('/{dataset}/dimensions',
                controller='dimension', action='index')

    map.connect('/{dataset}/{dimension}.distinct.json',
                controller='dimension', action='distinct', format='json')
    map.connect('/{dataset}/{dimension}.distinct',
                controller='dimension', action='distinct')

    map.connect('/{dataset}/{dimension}.json',
                controller='dimension', action='view', format='json')
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
