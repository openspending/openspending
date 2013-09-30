from datetime import datetime

from sqlalchemy import *
from migrate import *
import uuid

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    account = Table('account', meta, autoload=True)

    # Column that stores the user's secret api key
    secret_api_key = Column('secret_api_key', Unicode, default=unicode(uuid.uuid4()))
    secret_api_key.create(account)


def downgrade(migrate_engine):
    raise NotImplementedError()
