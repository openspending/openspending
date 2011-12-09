from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)

    ckan_uri = Column('ckan_uri', Unicode())
    ckan_uri.create(dataset) 

