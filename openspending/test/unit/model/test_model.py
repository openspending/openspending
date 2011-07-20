from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

class TestModel(DatabaseTestCase):
    def setup(self):
        super(TestModel, self).setup()
        model.Dataset(name='testdataset').save()

    # Our model classes find and find_one do not behave consistently.
    # If we use __getitem__ on a cursor it will not recognize the
    # argument 'as_class' we pass to pymongo in model.Base.find().
    # The reason is that the cursor is cloned inside pymongo which
    # doesn't pass as_class. See:
    #   http://jira.mongodb.org/browse/PYTHON-173
    #
    # The following four tests ensure that we detect any changes in this
    # behaviour.

    def test_model_find_one_returns_instance(self):
        dataset = model.Dataset.find_one()
        assert isinstance(dataset, model.Dataset), \
               "find_one() doesn't return an instance!"

    def test_model_find_next_returns_instance(self):
        dataset = model.Dataset.find().next()
        assert isinstance(dataset, model.Dataset), \
               "find().next() doesn't return an instance!"

    def test_model_find_iterator_returns_instance(self):
        dataset = [x for x in model.Dataset.find()][0]
        assert isinstance(dataset, model.Dataset), \
               "[x for x in find()][0] doesn't return an instance!"

    def test_model_find_slice_doesnt_return_instance(self):
        dataset = model.Dataset.find()[0]
        assert not isinstance(dataset, model.Dataset), \
               "find()[0] returns an instance!"

class TestModelAsDict(DatabaseTestCase):

    def setup(self):
        super(TestModelAsDict, self).setup()
        self.ds = model.Dataset(name="foo", label="Foo",
                                currency="GBP", description="Blah...")
        self.ds.save()

    def test_dictlike(self):
        for field in ['_id', 'name', 'currency', 'label', 'description']:
            assert field in self.ds, (field, self.ds)
