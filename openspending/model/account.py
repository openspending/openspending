import uuid

from mongo import Base, dictproperty


class Account(Base):
    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')
    email = dictproperty('email')
    password_hash = dictproperty('password_hash')
    api_key = dictproperty('api_key')

    def __init__(self, *args, **kwargs):
        self.api_key = str(uuid.uuid4())
        super(Account, self).__init__(*args, **kwargs)
    
    @classmethod
    def by_name(cls, name):
        return cls.find_one({'name': name})

    @classmethod
    def by_api_key(cls, api_key):
        return cls.c.find_one({'api_key': api_key})

