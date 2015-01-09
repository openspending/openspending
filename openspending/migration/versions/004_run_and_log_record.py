from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    dataset = Table('dataset', meta, autoload=True)
    source = Table('source', meta, autoload=True)

    run_table = Table('run', meta,
        Column('id', Integer, primary_key=True),
        Column('operation', Unicode(2000)),
        Column('status', Unicode(2000)),
        Column('time_start', DateTime),
        Column('time_end', DateTime),
        Column('dataset_id', Integer, 
            ForeignKey('dataset.id'), nullable=True),
        Column('source_id', Integer, 
            ForeignKey('source.id'), nullable=True)
        )
    run_table.create()

    run_log_record = Table('log_record', meta,
        Column('id', Integer, primary_key=True),
        Column('run_id', Integer, ForeignKey('run.id')),
        Column('category', Unicode),
        Column('level', Unicode),
        Column('message', Unicode),
        Column('timestamp', DateTime),
        Column('error', Unicode),
        Column('row', Integer),
        Column('attribute', Unicode),
        Column('column', Unicode),
        Column('data_type', Unicode),
        Column('value', Unicode)
        )
    run_log_record.create()

