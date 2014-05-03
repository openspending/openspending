from datetime import datetime

from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table, Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, DateTime

from openspending.model.account import Account
from openspending.model import meta as db

# Badges and dataset share a many to many relationship
# therefore we need to create an associate table
badges_on_datasets = Table('badges_on_datasets', db.metadata,
                           Column('badge_id',
                                  Integer,
                                  ForeignKey('badge.id')),
                           Column('dataset_id',
                                  Integer,
                                  ForeignKey('dataset.id'))
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

    id = Column(Integer, primary_key=True)

    # Primary information for this badge
    label = Column(Unicode)
    image = Column(Unicode)
    description = Column(Unicode)

    # Define relationship with datasets via the associate table
    datasets = relationship("Dataset",
                            secondary=badges_on_datasets,
                            backref=backref('badges', lazy='dynamic'))

    # Creator (and relationship)
    creator_id = Column(Integer, ForeignKey('account.id'))
    creator = relationship(Account,
                           backref=backref('badge_creations',
                                           lazy='dynamic'))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __init__(self, label, image, description, creator):
        """
        Initialize a badge object.
        Badge label should be a representative title for the badge
        Image should be a small, representative image for the badge
        Description describes the purpose of the badge in more detail
        Creator is the user who created the badge.
        """

        self.label = label
        self.image = image
        self.description = description
        self.creator = creator

    def __repr__(self):
        return "<Badge(%s)>" % self.label

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

    def as_dict(self, short=False):
        """
        A dictionary representation of the badge. This can return a long
        version containing all interesting fields or a short version containing
        only id, label and image.
        """
        badge = {
            "id": self.id,
            "label": self.label,
            "image": self.image,
        }
        if not short:
            badge.update({
                "description": self.description,
                "datasets": [ds.name for ds in self.datasets],
                "created_at": self.created_at
            })

        return badge
