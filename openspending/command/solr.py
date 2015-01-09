from openspending.lib import solr_util as solr

from openspending.command.util import create_submanager

manager = create_submanager(description='Solr index operations')


@manager.command
def load(dataset):
    """ Load data for dataset into Solr """
    solr.build_index(dataset)


@manager.command
def loadall():
    """ Load data for all datasets into Solr """
    solr.build_all_index()


@manager.command
def delete(dataset):
    """ Delete data for dataset from Solr """
    solr.drop_index(dataset)


@manager.command
def optimize():
    """ Optimize the Solr index """
    solr.get_connection().optimize()


@manager.command
def clean():
    """ Empty/reset the Solr index """
    s = solr.get_connection()
    s.delete_query('*:*')
    s.commit()
