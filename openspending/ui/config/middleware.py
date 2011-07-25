"""Pylons middleware initialization"""
import logging, sys

from beaker.middleware import CacheMiddleware, SessionMiddleware
from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool

from pylons import config
from pylons.middleware import ErrorHandler, StatusCodeRedirect
from pylons.wsgiapp import PylonsApp
from routes.middleware import RoutesMiddleware

from repoze.who.middleware import PluggableAuthenticationMiddleware
from repoze.who.interfaces import IIdentifier, IChallenger
from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.redirector import RedirectorPlugin
from repoze.who.plugins.htpasswd import HTPasswdPlugin
from repoze.who.classifiers import (default_request_classifier,
                                    default_challenge_decider)
from repoze.who.plugins.friendlyform import FriendlyFormPlugin

from openspending.plugins import core as plugins
from openspending.plugins.interfaces import IMiddleware

from openspending.ui.config.environment import load_environment
from openspending.ui.lib.authenticator import (UsernamePasswordAuthenticator,
                                               ApiKeyAuthenticator)

def make_app(global_conf, full_stack=True, static_files=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether this application provides a full WSGI stack (by default,
        meaning it handles its own exceptions and errors). Disable
        full_stack when this application is "managed" by another WSGI
        middleware.

    ``static_files``
        Whether this application serves its own static files; disable
        when another web server is responsible for serving them.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).

    """
    # Configure the Pylons environment
    load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp()

    # Routing/Session/Cache Middleware
    app = RoutesMiddleware(app, config['routes.map'])
    app = SessionMiddleware(app, config)
    app = CacheMiddleware(app, config)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)
    basicauth = BasicAuthPlugin('OpenSpending')
    auth_tkt = AuthTktCookiePlugin('RANDOM_KEY_THAT_ONLY_LOOKS_LIKE_A_PLACEHOLDER',
            cookie_name = 'openspending_login', timeout = 86400 * 90,
            reissue_time = 3600)
    form = FriendlyFormPlugin(
            '/login',
            '/perform_login',
            '/after_login',
            '/logout',
            '/after_logout',
            rememberer_name='auth_tkt')
    identifiers = [('auth_tkt', auth_tkt),
                   ('basicauth', basicauth),
                   ('form', form)]
    authenticators = [('auth_tkt', auth_tkt),
                      ('username', UsernamePasswordAuthenticator()),
                      ('apikey', ApiKeyAuthenticator())]
    challengers = [('form', form),
                   ('basicauth', basicauth)]
    log_stream = sys.stdout
    app = PluggableAuthenticationMiddleware(
        app, identifiers, authenticators, challengers, [],
        default_request_classifier,
        default_challenge_decider,
        log_stream = log_stream,
        log_level = logging.WARN
        )

    if asbool(full_stack):
        # Handle Python exceptions
        app = ErrorHandler(app, global_conf, **config['pylons.errorware'])

        # Display error documents for 401, 403, 404 status codes (and
        # 500 when debug is disabled)
        if asbool(config['debug']):
            app = StatusCodeRedirect(app)
        else:
            app = StatusCodeRedirect(app, [400, 401, 403, 404, 500])

    # Establish the Registry for this application
    app = RegistryManager(app)

    if asbool(static_files):
        max_age = None if asbool(config['debug']) else 3600

        # Serve static files
        static_app = StaticURLParser(
            config['pylons.paths']['static_files'],
            cache_max_age=max_age
        )
        static_parsers = [static_app, app]
        app = Cascade(static_parsers)

    # Plugin middleware
    for plugin in plugins.PluginImplementations(IMiddleware):
        app = plugin.configure(app)

    return app
