import datetime

import pymongo

from mongo import Base, dictproperty


class Changeset(Base):
    '''Metadata and details of a change to the Domain Model.'''

    id = dictproperty('_id')
    author = dictproperty('author')
    message = dictproperty('message')
    timestamp = dictproperty('timestamp')

    def __init__(self, *args, **kwargs):
        self.timestamp = datetime.datetime.now().isoformat()
        super(Changeset, self).__init__(*args, **kwargs)

    # This is really ugly
    def _get_manifest(self):
        if not hasattr(self, '_manifest'):
            if self.id:
                self._manifest = list(ChangeObject.find({'changeset': self}))
            else:
                self._manifest = []
        return self._manifest

    def _set_manifest(self, v):
        self._manifest = v

    manifest = property(_get_manifest, _set_manifest)

    def save(self):
        super(Changeset, self).save()
        for change_obj in self.manifest:
            change_obj.changeset = self
            change_obj.save()

    @classmethod
    def youngest(cls):
        '''Get the most recent Changeset'''
        out = list(cls.c.find(as_class=cls).sort('timestamp', pymongo.DESCENDING).limit(1))
        if out:
            return out[0]


class ChangeObject(Base):
    class DataType(object):
        FULL = 'full'
        DIFF = 'diff'
    class OperationType(object):
        CREATE = 'create'
        UPDATE = 'update'
        DELETE = 'delete'

    id = dictproperty('_id')
    operation_type = dictproperty('operationtype')
    data_type = dictproperty('datatype')
    data = dictproperty('data')
    object_id = dictproperty('object_id')
    changeset = dictproperty('changeset')

    def __init__(self, *args, **kwargs):
        options = {
            'data_type': self.DataType.FULL,
            'operation_type': self.OperationType.CREATE
        }
        options.update(kwargs)
        super(ChangeObject, self).__init__(*args, **options)


class Revisioned(Base):
    is_revisioned = True

    def save(self, changeset=None):
        '''Save the object with revisioning if `changeset` provided'''
        if not self.id:
            optype = ChangeObject.OperationType.UPDATE
        else:
            optype = ChangeObject.OperationType.CREATE

        super(Revisioned, self).save()

        if changeset:
            co = ChangeObject(
                object_id=[self.c.name, self.id],
                data=dict(self),
                operation_type=optype,
                changeset=changeset
            )
            changeset.manifest.append(co)
            changeset.save()
