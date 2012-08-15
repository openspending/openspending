from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)

    serp_title = Column('serp_title', Unicode())
    serp_title.create(dataset)

    serp_teaser = Column('serp_teaser', Unicode())
    serp_teaser.create(dataset) 

