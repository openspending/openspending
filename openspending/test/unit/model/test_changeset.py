from openspending.lib import json
from openspending.model import Changeset, ChangeObject, Entry
from openspending.test import DatabaseTestCase

class TestChangeset(DatabaseTestCase):

    def test_01(self):
        cs = Changeset()
        assert cs.id == None
        cs.author = u'annakarenina'
        cs.save()

        out = Changeset.find_one({'_id': cs.id})
        assert cs.author == u'annakarenina'
        assert cs.message == None
        assert cs.timestamp
        assert cs.manifest == []

    def test_02(self):
        co = ChangeObject()
        objectid = (u'package', 1, 2, 3)
        co.object_id = objectid
        co.operation = ChangeObject.OperationType.CREATE
        co.data = json.dumps({
            'field1': 'aaaaaa',
            'field2': 'bbbbbb'
            }, sort_keys=True)
        cs = Changeset()
        cs.manifest.append(co)
        cs.author = 'xyz'
        cs.save()

        changeobjs = list(ChangeObject.find())
        assert len(changeobjs) == 1
        co = changeobjs[0]
        assert co.changeset.id == cs.id
        out = Changeset.by_id(cs.id)
        assert len(out.manifest) == 1
        assert out.manifest[0].object_id == co.object_id

    def test_03_changeset_auto_created(self):
        c1 = Changeset(author='me')
        e1 = Entry(name='infinitejest', label='abc')
        e1.save(c1)

        out = Changeset.youngest()

        co = out.manifest[0]

        assert co.object_id == ['entry', e1.id]
        assert co.data['name'] == 'infinitejest'

        oute1 = Entry.by_id(e1.id)
        oute1.name = 'hamlet'
        ec2 = Entry(name='horatio')
        cs2 = Changeset(author='you')
        oute1.save(cs2)
        ec2.save(cs2)

        out = Changeset.youngest()
        assert len(out.manifest) == 2
        co = out.manifest[0]
        assert co.object_id == ['entry', e1.id]
        assert co.data['name'] == 'hamlet'

