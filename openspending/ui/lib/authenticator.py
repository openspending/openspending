from zope.interface import implements
from repoze.who.interfaces import IAuthenticator
from paste.httpheaders import AUTHORIZATION

from openspending.model import Account
from openspending.ui.lib.security import check_password_hash


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

class ApiKeyAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        """ 
        Generates a signature for a request and compares it against 
        the signature provided as a GET parameter.
        The hashing of the signatures is done using MD5.
        The way to generate a signature is concatenating in a string
        the secret_api_key for the user with the sorted keys of the request
        and their values. For example (no valid values):

        'c9502d56-446e-49de-9ccc-f9daaeb2f114apikey032020d2-ab08-4d53-b6c3- \
        c890510d92fbcsv_filehttp://mk.ucant.org/info/data/sample-openspendi \
        ng-dataset.csvmetadatahttps://dl.dropbox.com/u/3250791/sample-opens \
        pending-model.json'
        """
        import hashlib

        if not 'apikey' in identity or not 'signature' in identity or not Account.by_api_key(identity['apikey']):
            return None

        user = Account.by_api_key(identity['apikey'])
        m = hashlib.md5()
        query = [user.secret_api_key]
        for key in sorted(identity.keys()):
            if key != 'signature':
                query.append(key)
                query.append(identity[key])

        m.update(''.join(query))
        computed_signature = m.hexdigest()
        if computed_signature == identity['signature']:
            return user.name
        return None