"""SQLAlchemy Metadata and Session object"""

from sqlalchemy import MetaData
from sqlalchemy import Table, Column, ForeignKey, Integer, Boolean
from sqlalchemy import Unicode, UnicodeText, Float, DateTime
from sqlalchemy import or_, and_
from sqlalchemy.orm import reconstructor, aliased

from sqlalchemy import orm
from sqlalchemy import func, select
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy


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

