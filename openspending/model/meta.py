"""SQLAlchemy Metadata and Session object"""

from sqlalchemy import MetaData
from sqlalchemy import Table, Column, ForeignKey, Integer, Boolean
from sqlalchemy import or_, and_

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
metadata = MetaData()
