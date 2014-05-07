from sqlalchemy.orm import sessionmaker, scoped_session
from openspending.model import meta as db

# We need to import all models to make them discoverable model init
# (engine creation).
from openspending.model.account import Account  # NOQA
from openspending.model.badge import Badge  # NOQA
from openspending.model.dataset import (Dataset, DatasetLanguage,  # NOQA
                                        DatasetTerritory)
from openspending.model.log_record import LogRecord  # NOQA
from openspending.model.run import Run  # NOQA
from openspending.model.source import Source  # NOQA
from openspending.model.view import View  # NOQA

# Silence SQLAlchemy warning:
import warnings
warnings.filterwarnings(
    'ignore',
    'Unicode type received non-unicode bind param value.')


def init_model(engine):
    """ Initialize the SQLAlchemy driver and session maker. """

    sm = sessionmaker(autoflush=True, bind=engine)
    db.engine = engine
    db.metadata.bind = engine
    db.session = scoped_session(sm)
