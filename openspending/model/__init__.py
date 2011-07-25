"""The application's model objects"""
import os.path

from pkg_resources import resource_listdir, resource_stream

import mongo
from mongo import Base
from dimension import Dimension
from dataset import Dataset
from classifier import Classifier
from entry import Entry
from entity import Entity
from account import Account
from changeset import Changeset, ChangeObject

def init_mongo(config):
    host = config.get('openspending.mongodb.host', 'localhost')
    port = config.get('openspending.mongodb.port', 27017)
    mongo.make_connection(host, port)
    mongo.db_name = config.get('openspending.mongodb.database', 'openspending')
    init_serverside_js()

def init_serverside_js():
    '''
    Store (and update) all server side javascript functions
    that are stored in openspending/model/serverside_js
    '''
    for filename in resource_listdir('openspending.model', 'serverside_js'):
        if filename.endswith('.js'):
            function_name = filename.rsplit('.js')[0]
            function_file = resource_stream('openspending.model',
                                            os.path.join('serverside_js',
                                                         filename))

            function_string = function_file.read()
            function_file.close()

            setattr(mongo.db().system_js, function_name, function_string)
