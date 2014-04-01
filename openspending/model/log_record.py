from datetime import datetime

from openspending.model import meta as db
from openspending.model.run import Run


class LogRecord(db.Model):
    __tablename__ = 'log_record'

    CATEGORY_SYSTEM = 'system'
    CATEGORY_MODEL = 'model'
    CATEGORY_DATA = 'data'

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'))

    category = db.Column(db.Unicode)
    level = db.Column(db.Unicode)
    message = db.Column(db.Unicode)
    error = db.Column(db.Unicode)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    row = db.Column(db.Integer)
    attribute = db.Column(db.Unicode)
    column = db.Column(db.Unicode)
    data_type = db.Column(db.Unicode)
    value = db.Column(db.Unicode)

    run = db.relationship(Run, backref=db.backref('records',
                                                  lazy='dynamic'))

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
