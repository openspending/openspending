from sqlalchemy import Boolean, Column, MetaData, Table


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    account = Table('account', meta, autoload=True)

    termsc = Column('terms', Boolean, default=False)
    termsc.create(account, populate_default=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    account = Table('account', meta, autoload=True)

    account.c.terms.drop()
