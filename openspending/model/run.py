from datetime import datetime

from openspending.model import meta as db
from openspending.model.dataset import Dataset
from openspending.model.source import Source


class Run(db.Model):

    """ A run is a generic grouping object for background operations
    that perform logging to the frontend. """

    __tablename__ = 'run'

    # Status values
    STATUS_RUNNING = 'running'
    STATUS_COMPLETE = 'complete'
    STATUS_FAILED = 'failed'
    STATUS_REMOVED = 'removed'

    # Operation values for database, two operations possible
    OPERATION_SAMPLE = 'sample'
    OPERATION_IMPORT = 'import'

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
                              backref=db.backref(
                                  'runs',
                                  order_by='Run.time_start.desc()',
                                  lazy='dynamic'))
    source = db.relationship(Source,
                             backref=db.backref(
                                 'runs',
                                 order_by='Run.time_start.desc()',
                                 lazy='dynamic'))

    def __init__(self, operation, status, dataset, source):
        self.operation = operation
        self.status = status
        self.dataset = dataset
        self.source = source

    @property
    def successful_sample(self):
        """
        Returns True if the run was a sample operation (not full import)
        and ran without failures.
        """
        return self.operation == self.OPERATION_SAMPLE and \
            self.status == self.STATUS_COMPLETE

    @property
    def successful_load(self):
        """
        Returns True if the run was an import operation (not a sample)
        and ran without failures.
        """
        return self.operation == self.OPERATION_IMPORT and \
            self.status == self.STATUS_COMPLETE

    @property
    def is_running(self):
        """
        Returns True if the run is currently running
        """
        return self.status == self.STATUS_RUNNING

    @classmethod
    def by_id(cls, id):
        return db.session.query(cls).filter_by(id=id).first()

    def __repr__(self):
        return "<Run(%s,%s)>" % (self.source.id, self.id)
