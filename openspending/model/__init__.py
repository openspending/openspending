"""The application's model objects"""
from sqlalchemy import orm

from openspending.model import meta as db
from openspending.model.attribute import Attribute
from openspending.model.dimension import AttributeDimension, \
        CompoundDimension, Measure, Dimension, DateDimension
from openspending.model.dataset import Dataset
from openspending.model.dataset_language import DatasetLanguage
from openspending.model.dataset_territory import DatasetTerritory
from openspending.model.account import Account
from openspending.model.source import Source
from openspending.model.run import Run
from openspending.model.log_record import LogRecord
from openspending.model.view import View

# shut up useless SA warning:
import warnings
warnings.filterwarnings('ignore', 'Unicode type received non-unicode bind param value.')


def init_model(engine):
    """ Initialize the SQLAlchemy driver and session maker. """
    #if db.session is not None:
    #    return
    sm = orm.sessionmaker(autoflush=True, bind=engine)
    db.engine = engine
    db.metadata.bind = engine
    db.session = orm.scoped_session(sm)
