from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)

    category = Column('category', Unicode())
    category.create(dataset) 

    u = dataset.update(values={'category': 'other'})
    migrate_engine.execute(u)
