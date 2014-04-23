"""SQLAlchemy Metadata and Session object"""

from sqlalchemy import MetaData
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base


# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
metadata = MetaData()


class Model(object):

    """Baseclass for custom user models."""

    query_class = orm.Query
    query = None

Model = declarative_base(cls=Model, name='Model',
                         metadata=metadata)
