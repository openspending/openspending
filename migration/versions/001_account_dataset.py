from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta,
                    Column('id', Integer, primary_key=True),
                    Column('name', Unicode(255), unique=True),
                    Column('label', Unicode(2000)),
                    Column('description', Unicode),
                    Column('currency', Unicode),
                    Column('default_time', Unicode),
                    Column('data', Text),
                    )

    account = Table('account', meta,
                    Column('id', Integer, primary_key=True),
                    Column('name', Unicode(255), unique=True),
                    Column('fullname', Unicode(2000)),
                    Column('email', Unicode(2000)),
                    Column('password', Unicode(2000)),
                    Column('api_key', Unicode(2000)),
                    Column('private_api_key', Unicode(2000)),
                    Column('admin', Boolean, default=False),
                    )

    dataset.create()
    account.create()

def downgrade(migrate_engine):
    raise NotImplementedError()
