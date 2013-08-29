from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    account = Table('account', meta, autoload=True)

    # Column that stores the user's private api key
    private_api_key = Column('private_api_key', Unicode)
    private_api_key.create(account)


def downgrade(migrate_engine):
    raise NotImplementedError()
