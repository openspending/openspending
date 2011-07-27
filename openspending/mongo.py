import os.path
from pkg_resources import resource_listdir, resource_stream

from pymongo import Connection, errors

connection = None
db = None

def configure(config):
    host = config.get('openspending.mongodb.host', 'localhost')
    port = config.get('openspending.mongodb.port', 27017)
    db_name = config.get('openspending.mongodb.database', 'openspending')
    establish_connection(host, port, db_name)
    _init_serverside_js()

def establish_connection(host, port, database):
    global connection
    global db
    connection = Connection(host, port)
    # connection.document_class = Base
    db = connection[database]

def drop_db():
    connection.drop_database(db.name)

def drop_collections():
    """
    Drop all app collections from the database. This is far faster than
    simply calling mongo.drop_db.
    """
    for name in db.collection_names():
        if name not in ['system.indexes', 'system.js']:
            db.drop_collection(name)

def _init_serverside_js():
    '''
    Store (and update) all server side javascript functions
    that are stored in openspending/model/serverside_js
    '''
    for filename in resource_listdir('openspending.model', 'serverside_js'):
        if filename.endswith('.js'):
            function_name = filename.rsplit('.js')[0]
            function_file = resource_stream(
                'openspending.model', os.path.join('serverside_js', filename)
            )

            function_string = function_file.read()
            function_file.close()

            setattr(db.system_js, function_name, function_string)