from datetime import datetime
from sqlalchemy.orm import reconstructor, relationship, backref
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, Boolean, DateTime
from sqlalchemy.sql.expression import false, or_
from sqlalchemy.ext.associationproxy import association_proxy

from openspending.core import db

from openspending.model.model import Model
from openspending.model.common import (MutableDict, JSONType,
                                       DatasetFacetMixin)


class Dataset(db.Model):

    """ The dataset is the core entity of any access to data. All
    requests to the actual data store are routed through it, as well
    as data loading and model generation.

    The dataset keeps an in-memory representation of the data model
    (including all dimensions and measures) which can be used to
    generate necessary queries.
    """
    __tablename__ = 'dataset'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    label = Column(Unicode(2000))
    description = Column(Unicode())
    currency = Column(Unicode())
    default_time = Column(Unicode())
    schema_version = Column(Unicode())
    category = Column(Unicode())
    serp_title = Column(Unicode(), nullable=True)
    serp_teaser = Column(Unicode(), nullable=True)
    private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    data = Column(MutableDict.as_mutable(JSONType), default=dict)

    languages = association_proxy('_languages', 'code')
    territories = association_proxy('_territories', 'code')

    def __init__(self, data):
        self.data = data.copy()
        dataset = self.data['dataset']
        del self.data['dataset']
        self.label = dataset.get('label')
        self.name = dataset.get('name')
        self.description = dataset.get('description')
        self.currency = dataset.get('currency')
        self.category = dataset.get('category')
        self.serp_title = dataset.get('serp_title')
        self.serp_teaser = dataset.get('serp_teaser')
        self.default_time = dataset.get('default_time')
        self.languages = dataset.get('languages', [])
        self.territories = dataset.get('territories', [])
        self._load_model()

    @property
    def model_data(self):
        model = self.data.copy()
        model['dataset'] = self.as_dict()
        return model

    @property
    def mapping(self):
        return self.data.get('mapping', {})

    @reconstructor
    def _load_model(self):
        self.model = Model(self)

    def touch(self):
        """ Update the dataset timestamp. This is used for cache
        invalidation. """
        self.updated_at = datetime.utcnow()
        db.session.add(self)

    @property
    def has_badges(self):
        """
        Property that returns True if the dataset has been given any badges
        """
        # Cast the badge count as a boolean and return it
        return bool(self.badges.count())

    def can_read(self, user):
        """
        Permissions for dataset access (read).
        Returns a boolean indicating if a user may read the dataset
        """
        # If the dataset is not private anybody can read
        # If the datset is private only users who can update it can read it
        return not self.private or self.can_update(user)

    def can_update(self, user):
        """
        Permissions for dataset updates.
        Returns a boolean indicating if a user may update the dataset
        """
        # User needs to be logged in and either admin or one of the dataset
        # managers
        return user is not None and (
            user.admin or
            db.session.query(  # Check if the user exists in managers
                self.managers.filter_by(id=user.id).exists()).first()
        )

    def can_delete(self, user):
        """
        Permissions for dataset removal (delete).
        Returns a boolean indicating if a user may delete the dataset.
        """
        # Users who can update the dataset can also delete it
        return self.can_update(user)

    def __repr__(self):
        return "<Dataset(%r,%r)>" % (self.id, self.name)

    def as_dict(self):
        return {
            'label': self.label,
            'name': self.name,
            'description': self.description,
            'default_time': self.default_time,
            'schema_version': self.schema_version,
            'currency': self.currency,
            'category': self.category,
            'serp_title': self.serp_title,
            'serp_teaser': self.serp_teaser,
            'timestamps': {
                'created': self.created_at,
                'last_modified': self.updated_at
            },
            'languages': list(self.languages),
            'territories': list(self.territories),
            'badges': [b.as_dict(short=True) for b in self.badges]
        }

    @classmethod
    def all_by_account(cls, account):
        """ Query available datasets based on dataset visibility. """
        from openspending.model.account import Account
        criteria = [cls.private == false()]
        if account is not None and account.is_authenticated():
            criteria += ["1=1" if account.admin else "1=2",
                         cls.managers.any(Account.id == account.id)]
        q = db.session.query(cls).filter(or_(*criteria))
        q = q.order_by(cls.label.asc())
        return q

    @classmethod
    def by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()


class DatasetLanguage(db.Model, DatasetFacetMixin):
    __tablename__ = 'dataset_language'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(Dataset, backref=backref('_languages', lazy=False))

    def __init__(self, code):
        self.code = code


class DatasetTerritory(db.Model, DatasetFacetMixin):
    __tablename__ = 'dataset_territory'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey('dataset.id'))
    dataset = relationship(Dataset, backref=backref('_territories',
                                                    lazy=False))

    def __init__(self, code):
        self.code = code
