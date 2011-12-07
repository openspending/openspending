from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)

    dataset_language = Table('dataset_language', meta,
        Column('id', Integer, primary_key=True),
        Column('code', Unicode),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, onupdate=datetime.utcnow),
        Column('dataset_id', Integer, ForeignKey('dataset.id'))
        )
    dataset_language.create()
    
    dataset_country = Table('dataset_country', meta,
        Column('id', Integer, primary_key=True),
        Column('code', Unicode),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, onupdate=datetime.utcnow),
        Column('dataset_id', Integer, ForeignKey('dataset.id'))
        )
    dataset_country.create()

