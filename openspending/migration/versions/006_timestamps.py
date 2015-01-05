from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    dataset = Table('dataset', meta, autoload=True)
    created_at = Column('created_at', DateTime, default=datetime.utcnow)
    created_at.create(dataset) 
    updated_at = Column('updated_at', DateTime, onupdate=datetime.utcnow)
    updated_at.create(dataset) 

    source = Table('source', meta, autoload=True)
    updated_at = Column('updated_at', DateTime, onupdate=datetime.utcnow)
    updated_at.create(source) 
