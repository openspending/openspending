from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset

class DatasetCountry(db.Model):
    __tablename__ = 'dataset_country'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship(Dataset, backref=db.backref('countries',
                          lazy='dynamic'))

    def __init__(self, dataset, code):
        self.dataset = dataset
        self.code = code


