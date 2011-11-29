from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.source import Source


class Run(db.Model):
    """ A run is a generic grouping object for background operations
    that perform logging to the frontend. """

    __tablename__ = 'run'

    STATUS_RUNNING = 'running'
    STATUS_COMPLETE = 'complete'
    STATUS_FAILED = 'failed'

    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.Unicode(2000))
    status = db.Column(db.Unicode(2000))
    time_start = db.Column(db.DateTime, default=datetime.utcnow)
    time_end = db.Column(db.DateTime)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'),
                           nullable=True)

    dataset = db.relationship(Dataset,
                              backref=db.backref('runs',
                                  order_by='Run.time_start.desc()',
                                  lazy='dynamic'))
    source = db.relationship(Source,
                              backref=db.backref('runs', 
                                  order_by='Run.time_start.desc()',
                                  lazy='dynamic'))

    def __init__(self, operation, status, dataset, source):
        self.operation = operation
        self.status = status
        self.dataset = dataset
        self.source = source

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    def __repr__(self):
        return "<Run(%s,%s)>" % (self.source.id, self.id)


