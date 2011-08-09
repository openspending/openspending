from zope.interface import implements
from repoze.who.interfaces import IAuthenticator
from paste.httpheaders import AUTHORIZATION

from openspending.model import account
from openspending.ui.lib.security import check_password_hash


class UsernamePasswordAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        if not 'login' in identity or not 'password' in identity:
            return None
        acc = account.find_one_by('name', identity['login'])
        if acc is None:
            return None
        if check_password_hash(acc['password_hash'], identity['password']):
            return acc['name']
        return None

class ApiKeyAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        authorization = AUTHORIZATION(environ)
        try:
            authmeth, auth = authorization.split(' ', 1)
        except ValueError: # not enough values to unpack
            return None
        if authmeth.lower() == 'apikey':
            acc = account.find_one_by('api_key', auth.strip())
            if acc is not None:
                return acc['name']


