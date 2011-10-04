"""The application's model objects"""
from sqlalchemy import orm

from openspending.model import meta as db
from openspending.model.attribute import Attribute
from openspending.model.dimension import ValueDimension, ComplexDimension, Metric
from openspending.model.dataset import Dataset

def init_model(engine):
    """ Initialize the SQLAlchemy driver and session maker. """
    if db.session is not None:
        return
    sm = orm.sessionmaker(autoflush=True, bind=engine)
    db.engine = engine
    db.metadata.bind = engine
    db.session = orm.scoped_session(sm)
    


