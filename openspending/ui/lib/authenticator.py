from zope.interface import implements
from repoze.who.interfaces import IAuthenticator, IIdentifier
from paste.httpheaders import AUTHORIZATION

from openspending.model import Account
from openspending.ui.lib.security import check_password_hash

import logging
log = logging.getLogger(__name__)

class UsernamePasswordAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        if not 'login' in identity or not 'password' in identity:
            return None
        account = Account.by_name(identity['login'])
        if account is None:
            return None
        if account.password is None:
            return None
        if check_password_hash(account.password, identity['password']):
            return account.name
        return None


class ApiKeyIdentifier(object):
    implements(IIdentifier)

    def identify(self, environ):
        """
        Try to identify user based on api key authorization in header
        """

        # Get the authorization header as passed through paster
        authorization = AUTHORIZATION(environ)
        log.debug(authorization)
        # Split the authorization header value by whitespace
        try:
            method, auth = authorization.split(' ', 1)
        except ValueError:
            # not enough values to unpack
            return None

        # If authentication method is apikey we return the identity
        if method.lower() == 'apikey':
            return {'apikey': auth.strip()}

        # Return None if we get here (identity not found)
        return None

    def remember(self, environ, identity):
        """
        API key authentication headers user can use to make the system
        remember the user
        """

        # User cannot ask to be remembered since API key is the authentication
        # mechanism and must be used on every request (thus, no headers)
        return None

    def forget(self, environ, identity):
        """
        API key authentication headers user can use to make the system
        forget the user
        """

        # User cannot be remembered so there is no need to forget the user
        # either (and thus no header mechanism)
        return None

class ApiKeyAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        """
        Try to authenticate user based on api key identity
        """

        # If identity has apikey we get the account by the api key
        # and return none if no account or apikey is found is found
        if 'apikey' in identity:
            acc = Account.by_api_key(identity.get('apikey'))
            if acc is not None:
                return acc.name

        return None

