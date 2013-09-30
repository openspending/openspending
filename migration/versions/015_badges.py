from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)
    account = Table('account', meta, autoload=True)

    badge = Table('badge', meta,
        Column('id', Integer, primary_key=True),
        Column('label', Unicode),
        Column('image', Unicode),
        Column('description', Unicode),
        Column('creator_id', Integer, ForeignKey('account.id')),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, default=datetime.utcnow),
        )

    badge.create()

    badges_on_datasets = Table('badges_on_datasets', meta,
        Column('badge_id', Integer, ForeignKey('badge.id')),
        Column('dataset_id', Integer, ForeignKey('dataset.id'))
        )

    badges_on_datasets.create()

def downgrade(migrate_engine):
    raise NotImplementedError()



