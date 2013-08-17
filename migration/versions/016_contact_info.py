from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    account = Table('account', meta, autoload=True)

    # Column that stores the user's twitter handle
    twitter_handle = Column('twitter_handle', Unicode)
    twitter_handle.create(account)

    # Should email address be public?
    public_email = Column('public_email', Boolean, default=False)
    public_email.create(account)

    # Should twitter handle be public?
    public_twitter = Column('public_twitter', Boolean, default=False)
    public_twitter.create(account)

def downgrade(migrate_engine):
    raise NotImplementedError()
