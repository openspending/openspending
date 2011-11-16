from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)
    account = Table('account', meta, autoload=True)

    source_table = Table('source', meta,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('url', db.Unicode),
        db.Column('analysis', JSONType, default=dict),
        db.Column('created_at', db.DateTime, default=datetime.utcnow),
        db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id')),
        db.Column('creator_id', db.Integer, db.ForeignKey('account.id'))
        )

    source_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()



