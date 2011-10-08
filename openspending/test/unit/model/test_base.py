from openspending import mongo
from openspending.model import base
from openspending.model.base import ModelWrapper

from ... import TestCase, helpers as h

class TestBase(TestCase):

    # NB:
    #
    # Many functions in openspending.model.base are thin wrappers around, or
    # delegates to, Mongo functionality.
    #
    # As far as possible, we should not be testing Mongo functionality here,
    # but rather making sure that, e.g.:
    #   - keyword arguments we intend to curry are curried correctly
    #   - preflight checks of arguments are occuring
    #   - modification of return values is correct
    #
    # In order to do this we make extensive use of mock objects, and in theory
    # the following tests shouldn't even touch the database.

    def setup(self):
        super(TestBase, self).setup()
        self.patcher = h.patch('openspending.model.base.mongo.db', new=h.MagicMock())
        self.mock_db = self.patcher.start()
        self.mock_db.__getitem__.return_value = self.mock_collection = h.Mock()

    def teardown(self):
        self.patcher.stop()
        super(TestBase, self).teardown()

    def test_q_with_string(self):
        q = base.q({'_id': 'some_id'})
        h.assert_equal(q, {'_id': 'some_id'})

    def test_q_with_valid_objectid(self):
        q = base.q({'_id': '0123456789abcdef01234567'})
        h.assert_equal(q, {'_id': {'$in': ['0123456789abcdef01234567',
                                           mongo.ObjectId('0123456789abcdef01234567')]}})

    def test_q_with_other_keys(self):
        q = base.q({'_id': 'some_id', 'foo': 'bar'})
        h.assert_equal(q, {'_id': 'some_id'})

    def test_qs_with_strings(self):
        qs = base.qs([{'_id': 'some_id'}, {'_id': 'another'}])
        h.assert_equal(qs, {'_id': {'$in': ['some_id', 'another']}})

    def test_qs_with_mixed(self):
        qs = base.qs([{'_id': 'some_id'}, {'_id': '0123456789abcdef01234567'}])
        h.assert_equal(qs, {'_id': {'$in': ['some_id',
                                            '0123456789abcdef01234567',
                                            mongo.ObjectId('0123456789abcdef01234567')]}})

    def test_create(self):
        self.mock_collection.insert.return_value = 'foo_id'
        self.mock_collection.find_one.return_value = {'_id': 'foo_id', 'foo': 'bar'}
        res = base.create('test', {'foo': 'bar'})
        h.assert_equal(res, {'_id': 'foo_id', 'foo': 'bar'})
        self.mock_collection.insert.assert_called_with({'foo': 'bar'},
                                                       manipulate=True)
        self.mock_collection.find_one.assert_called_with({'_id': 'foo_id'})

    def test_distinct(self):
        self.mock_collection.distinct.return_value = ['bar', 'baz']
        h.assert_equal(base.distinct('test', 'foo'), ['bar', 'baz'])
        self.mock_collection.distinct.assert_called_with('foo')

    def test_find(self):
        self.mock_collection.find.return_value = [{'foo': 'bar'},
                                                  {'foo': 'baz'}]
        h.assert_equal(base.find('test'), [{'foo': 'bar'},
                                           {'foo': 'baz'}])
        self.mock_collection.find.assert_called_with(None)

    def test_find_one(self):
        self.mock_collection.find_one.return_value = {'foo': 'bar'}
        h.assert_equal(base.find_one('test'), {'foo': 'bar'})
        self.mock_collection.find_one.assert_called_with(None)

    def test_find_one_by(self):
        self.mock_collection.find_one.return_value = {'foo': 'bar'}
        h.assert_equal(base.find_one_by('test', 'foo', 'bar'), {'foo': 'bar'})
        self.mock_collection.find_one.assert_called_with({'foo': 'bar'})

    def test_get(self):
        self.mock_collection.find_one.return_value = {'_id': 'foo'}
        h.assert_equal(base.get('test', 'foo'), {'_id': 'foo'})
        self.mock_collection.find_one.assert_called_with({'_id': 'foo'})

    def test_get_ref_dict(self):
        res = base.get_ref_dict('test', {'_id': 'foo_id', 'foo': 'bar'})
        h.assert_equal(res['_id'], 'foo_id')
        h.assert_equal(res['foo'], 'bar')
        h.assert_equal(res['ref'], mongo.DBRef('test', 'foo_id'))

    def test_insert(self):
        self.mock_collection.insert.return_value = 'foo_id'
        res = base.insert('test', {'foo': 'bar'})
        h.assert_equal(res, 'foo_id')
        self.mock_collection.insert.assert_called_with({'foo': 'bar'},
                                                           manipulate=True)
    def test_remove(self):
        self.mock_collection.remove.return_value = None
        h.assert_equal(base.remove('test', {'foo': 'bar'}), None)
        self.mock_collection.remove.assert_called_with({'foo': 'bar'})

    def test_save(self):
        self.mock_collection.save.return_value = 'foo_id'
        h.assert_equal(base.save('test', {'_id': 'foo_id'}), 'foo_id')
        self.mock_collection.save.assert_called_with({'_id': 'foo_id'},
                                                     manipulate=True)

    def test_update_obj_with_id(self):
        spec = {'_id': 'foo_id', 'foo': 'bar'}
        doc = {'$set': {'bar': 'baz'}}
        self.mock_collection.update.return_value = 'foo_id'
        h.assert_equal(base.update('test', spec, doc), 'foo_id')
        self.mock_collection.update.assert_called_with({'_id': 'foo_id'}, doc)

    def test_update_obj_no_id(self):
        spec = {'name': 'foo', 'bar': 'baz'}
        doc = {'$set': {'bar': 'baz'}}
        self.mock_collection.update.return_value = 'foo_id'
        h.assert_equal(base.update('test', spec, doc), 'foo_id')
        self.mock_collection.update.assert_called_with(spec, doc)

class MockModelModule(object):
    pass

class TestModelWrapper(TestCase):
    def test_delegates_to_base(self):
        m = ModelWrapper(MockModelModule(), 'test')

        m.name = 'model_name'
        base.name = 'base_name'
        base.age = 12

        h.assert_equal(m.name, 'model_name')
        h.assert_equal(m.age, 12)

    def test_curries_functions_to_base(self):
        m = ModelWrapper(MockModelModule(), 'test')

        m.get_x = lambda x: x
        base.get_y = lambda c, x: (c, x)

        h.assert_equal(m.get_x('foo'), 'foo')
        h.assert_equal(m.get_y('bar'), ('test', 'bar'))

    @h.raises(AttributeError)
    def test_raises_original_attribute_error(self):
        m = ModelWrapper(MockModelModule(), 'test')
        m.foobar("hello")