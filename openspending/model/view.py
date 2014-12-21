from datetime import datetime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, Boolean, DateTime

from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.model.account import Account
from openspending.model.common import MutableDict, JSONType


class View(db.Model):

    """ A view stores a specific configuration of a visualisation widget. """

    __tablename__ = 'view'

    id = Column(Integer, primary_key=True)
    widget = Column(Unicode(2000))
    name = Column(Unicode(2000))
    label = Column(Unicode(2000))
    description = Column(Unicode())
    state = Column(MutableDict.as_mutable(JSONType), default=dict)
    public = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    account_id = Column(Integer, ForeignKey('account.id'), nullable=True)

    dataset = relationship(Dataset,
                           backref=backref('views',
                                           cascade='all,delete,delete-orphan',
                                           lazy='dynamic'))

    account = relationship(Account,
                           backref=backref('views',
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
