from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

class TestModel(model.mongo.Base):
    id = model.mongo.dictproperty('_id')
    name = model.mongo.dictproperty('name')

class TestBase(DatabaseTestCase):
    def setup(self):
        super(TestBase, self).setup()
        TestModel(name='testm').save()

    # Our model classes find and find_one didn't behave consistently in the
    # past, due to a bug in pymongo. This has now been fixed, but we keep the
    # old note and the tests here to detect any changes in this behaviour.
    #
    # OLD: If we use __getitem__ on a cursor it will not recognize the
    # argument 'as_class' we pass to pymongo in model.Base.find().
    # The reason is that the cursor is cloned inside pymongo which
    # doesn't pass as_class. See:
    #   http://jira.mongodb.org/browse/PYTHON-173
    #

    def test_model_find_one_returns_instance(self):
        m = TestModel.find_one()
        assert isinstance(m, TestModel), \
               "find_one() doesn't return an instance!"

    def test_model_find_next_returns_instance(self):
        m = TestModel.find().next()
        assert isinstance(m, TestModel), \
               "find().next() doesn't return an instance!"

    def test_model_find_iterator_returns_instance(self):
        m = [x for x in TestModel.find()][0]
        assert isinstance(m, TestModel), \
               "[x for x in find()][0] doesn't return an instance!"

    def test_model_find_slice_returns_instance(self):
        m = TestModel.find()[0]
        assert isinstance(m, TestModel), \
               "find()[0] doesn't returns an instance!"

class TestModelAsDict(DatabaseTestCase):

    def setup(self):
        super(TestModelAsDict, self).setup()
        self.ds = TestModel(name="foo", label="Foo",
                            currency="GBP", description="Blah...")
        self.ds.save()

    def test_dictlike(self):
        for field in ['_id', 'name', 'currency', 'label', 'description']:
            assert field in self.ds, (field, self.ds)

