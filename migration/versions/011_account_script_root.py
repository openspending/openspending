from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('account', meta, autoload=True)

    v = Column('script_root', Unicode())
    v.create(dataset)

