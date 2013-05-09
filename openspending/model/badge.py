from datetime import datetime

from openspending.model import Account, meta as db

# Badges and dataset share a many to many relationship
# therefore we need to create an associate table
badges_on_datasets = db.Table('badges_on_datasets', db.metadata,
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id')),
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id'))
)

class Badge(db.Model):
    """
    This model allows marking datasets with various badges.
    Examples could be "World Bank" - data verified by the World bank.

    Each badge has a name, a representative image and a description.
    Also stored for historical reasons are badge creator, creation time
    and modification date.
    """
    __tablename__ = 'badge'

    id = db.Column(db.Integer, primary_key=True)

    # Primary information for this badge
    name = db.Column(db.Unicode)
    image = db.Column(db.Unicode)
    description = db.Column(db.Unicode)
 
    # Define relationship with datasets via the associate table
    datasets = db.relationship("Dataset",
                               secondary=badges_on_datasets,
                               backref=db.backref('badges',
                                                  lazy='dynamic'))
   
    # Creator (and relationship)
    creator_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    creator = db.relationship(Account,
                              backref=db.backref('badge_creations',
                                                 lazy='dynamic'))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __init__(self, name, image, description, creator):
        """
        Initialize a badge object.
        Badge name should be a representative title for the badge
        Image should be a small, representative image for the badge
        Description describes the purpose of the badge in more detail
        Creator is the user who created the badge.
        """

        self.name = name
        self.image = image
        self.description = description
        self.creator = creator

    def __repr__(self):
        return "<Badge(%s)>" % self.name

    @classmethod
    def by_id(cls, id):
        """
        Find one badge given the id
        """
        return db.session.query(cls).filter_by(id=id).first()

    @classmethod
    def all(cls):
        """
        Find all badges
        """
        return db.session.query(cls)

    def as_dict(self):
        """
        A dictionary representation of the badge.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "dataset": self.dataset.name,
            "creator": self.creator.name
            "created_at": self.created_at
            }
