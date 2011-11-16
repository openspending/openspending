from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.account import Account


class Source(db.Model):
    __tablename__ = 'source'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship(Dataset,
                              backref=db.backref('sources', lazy='dynamic'))

    creator_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    creator = db.relationship(Account,
                              backref=db.backref('sources', lazy='dynamic'))

    def __init__(self, dataset, creator, url):
        self.dataset = dataset
        self.creator = creator
        self.url = url 

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()




