from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    account = Table('account', meta, autoload=True)
    account.c.secret_api_key.drop()

def downgrade(migrate_engine):
    raise NotImplementedError()
