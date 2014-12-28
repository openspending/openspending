from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)
    account = Table('account', meta, autoload=True)

    account_dataset_table = Table('account_dataset', meta,
            Column('dataset_id', Integer, ForeignKey('dataset.id'),
                primary_key=True),
            Column('account_id', Integer, ForeignKey('account.id'),
                primary_key=True)
        )

    account_dataset_table.create()
    private = Column('private', Boolean, default=False)
    private.create(dataset)
    u = dataset.update(values={'private': False})
    migrate_engine.execute(u)


def downgrade(migrate_engine):
    raise NotImplementedError()

