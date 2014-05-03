from datetime import datetime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, DateTime

from openspending.model import meta as db
from openspending.model.common import MutableDict, JSONType
from openspending.model.dataset import Dataset
from openspending.model.account import Account


class Source(db.Model):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    url = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    analysis = Column(MutableDict.as_mutable(JSONType), default=dict)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(
        Dataset,
        backref=backref('sources', lazy='dynamic',
                        order_by='Source.created_at.desc()'))

    creator_id = Column(Integer, ForeignKey('account.id'))
    creator = relationship(Account,
                           backref=backref('sources', lazy='dynamic'))

    def __init__(self, dataset, creator, url):
        self.dataset = dataset
        self.creator = creator
        self.url = url

    @property
    def loadable(self):
        """
        Returns True if the source is ready to be imported into the
        database. Does not not require a sample run although it
        probably should.
        """
        # It shouldn't be loaded again into the database
        if self.successfully_loaded:
            return False
        # It needs mapping to be loadable
        if not len(self.dataset.mapping):
            return False
        # There can be no errors in the analysis of the source
        if 'error' in self.analysis:
            return False
        # All is good... proceed
        return True

    @property
    def successfully_sampled(self):
        """
        Returns True if any of this source's runs have been
        successfully sampled (a complete sample run). This shows
        whether the source is ready to be imported into the database
        """
        return True in [r.successful_sample for r in self.runs]

    @property
    def is_running(self):
        """
        Returns True if any of this source's runs have the status
        'running'. This shows whether the loading has been started or not
        to help avoid multiple loads of the same resource.
        """
        return True in [r.is_running for r in self.runs]

    @property
    def successfully_loaded(self):
        """
        Returns True if any of this source's runs have been
        successfully loaded (not a sample and no errors). This
        shows whether the source has been loaded into the database
        """
        return True in [r.successful_load for r in self.runs]

    def __repr__(self):
        try:
            return "<Source(%s,%s)>" % (self.dataset.name, self.url)
        except:
            return ''

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    @classmethod
    def all(cls):
        return db.session.query(cls)

    def as_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "dataset": self.dataset.name,
            "created_at": self.created_at
        }
