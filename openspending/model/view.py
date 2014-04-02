from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.account import Account
from openspending.model.common import JSONType


class View(db.Model):
    """ A view stores a specific configuration of a visualisation widget. """

    __tablename__ = 'view'

    id = db.Column(db.Integer, primary_key=True)
    widget = db.Column(db.Unicode(2000))
    name = db.Column(db.Unicode(2000))
    label = db.Column(db.Unicode(2000))
    description = db.Column(db.Unicode())
    state = db.Column(JSONType, default=dict)
    public = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'),
                           nullable=True)

    dataset = db.relationship(Dataset,
                              backref=db.backref(
                                  'views',
                                  cascade='all,delete,delete-orphan',
                                  lazy='dynamic'))

    account = db.relationship(Account,
                              backref=db.backref(
                                  'views',
                                  cascade='all,delete,delete-orphan',
                                  lazy='dynamic'))

    def __init__(self):
        pass

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    @classmethod
    def by_name(cls, dataset, name):
        q = db.session.query(cls).filter_by(name=name)
        return q.filter_by(dataset=dataset).first()

    @classmethod
    def all_by_dataset(cls, dataset):
        return db.session.query(cls).filter_by(dataset=dataset)

    def as_dict(self):
        return {
            'id': self.id,
            'widget': self.widget,
            'name': self.name,
            'label': self.label,
            'description': self.description,
            'state': self.state,
            'public': self.public,
            'dataset': self.dataset.name,
            'account': self.account.name if self.account else None
        }

    def __repr__(self):
        return "<View(%s,%s)>" % (self.dataset.name, self.name)
