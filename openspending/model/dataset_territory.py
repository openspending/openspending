from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.common import DatasetFacetMixin

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, DateTime

class DatasetTerritory(db.Model, DatasetFacetMixin):
    __tablename__ = 'dataset_territory'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(Dataset, backref=backref('_territories',
                                                    lazy=False))

    def __init__(self, code):
        self.code = code
