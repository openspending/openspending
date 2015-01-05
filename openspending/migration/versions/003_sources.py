from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)
    account = Table('account', meta, autoload=True)

    source_table = Table('source', meta,
        Column('id', Integer, primary_key=True),
        Column('url', Unicode),
        Column('analysis', Unicode, default=dict),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('dataset_id', Integer, ForeignKey('dataset.id')),
        Column('creator_id', Integer, ForeignKey('account.id'))
        )

    source_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()



