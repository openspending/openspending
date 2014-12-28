from datetime import datetime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, DateTime

from openspending.core import db
from openspending.model.run import Run


class LogRecord(db.Model):
    __tablename__ = 'log_record'

    CATEGORY_SYSTEM = 'system'
    CATEGORY_MODEL = 'model'
    CATEGORY_DATA = 'data'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('run.id'))

    category = Column(Unicode)
    level = Column(Unicode)
    message = Column(Unicode)
    error = Column(Unicode)
    timestamp = Column(DateTime, default=datetime.utcnow)

    row = Column(Integer)
    attribute = Column(Unicode)
    column = Column(Unicode)
    data_type = Column(Unicode)
    value = Column(Unicode)

    run = relationship(Run, backref=backref('records', lazy='dynamic'))

    def __init__(self, run, category, level, message):
        self.run = run
        self.category = category
        self.level = level
        self.message = message

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    def __repr__(self):
        return "<LogRecord(%s:%s:%s:%s:%s)>" % (self.category, self.level,
                                                self.error, self.timestamp,
                                                self.message)
