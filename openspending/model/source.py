from datetime import datetime

from openspending.model import meta as db
from openspending.model.common import JSONType
from openspending.model.dataset import Dataset
from openspending.model.account import Account


class Source(db.Model):
    __tablename__ = 'source'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    analysis = db.Column(JSONType, default=dict)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship(Dataset,
                              backref=db.backref('sources', lazy='dynamic',
                                order_by='Source.created_at.desc()'))

    creator_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    creator = db.relationship(Account,
                              backref=db.backref('sources', lazy='dynamic'))

    def __init__(self, dataset, creator, url):
        self.dataset = dataset
        self.creator = creator
        self.url = url

    @property
    def loadable(self):
        if not len(self.dataset.mapping):
            return False
        if 'error' in self.analysis:
            return False
        return True

    def __repr__(self):
        return "<Source(%s,%s)>" % (self.dataset.name, self.url)

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    def as_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "dataset": self.dataset.name,
            "created_at": self.created_at
            }
