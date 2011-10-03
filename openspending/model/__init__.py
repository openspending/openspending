"""The application's model objects"""
from . import account
from . import classifier
from . import entry
from . import dataset
from . import dimension
from . import entity

from sqlalchemy import orm

from openspending.model import meta as db

def init_model(engine):
    """ Initialize the SQLAlchemy driver and session maker. """
    if db.session is not None:
        return
    sm = orm.sessionmaker(autoflush=True,
                          bind=engine)
    db.engine = engine
    db.session = orm.scoped_session(sm)


