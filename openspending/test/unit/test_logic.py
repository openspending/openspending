from bson.dbref import DBRef

from openspending import logic
from openspending import mongo
from openspending import model
from openspending.model import Classifier, Dataset, Entry
from openspending.test import DatabaseTestCase, helpers as h

class TestEntry(DatabaseTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()
        super(TestEntry, self).setup()

    def _make_dataset(self, name='testdataset'):
        dataset = Dataset.find_one(name)
        if dataset is None:
            dataset = Dataset(name=name)
            dataset.save()
        return dataset

    def _make_entry(self, name='testentry', region='testregion', amount=1.0,
                    dataset=None, **kwargs):
        if dataset is None:
            dataset = self._make_dataset()
        entry = Entry(name=name, region=region, amount=amount,
                      dataset=dataset, **kwargs)
        entry.save()
        return entry

    def test_distincts(self):
        testdataset = self._make_dataset(name='testdataset')
        self._make_entry(name='one', region="Region 1", region2="Region 2",
                         dataset=testdataset)
        self._make_entry(name='two', region="Region 2", region2="Region 3",
                         dataset=testdataset)

        h.assert_true('compute_distincts' in mongo.db.system_js.list())

        # compute a distincts collection
        mongo.db.system_js.compute_distincts('testdataset')
        h.assert_true('distincts__testdataset' in mongo.db.collection_names())

        # test the distincts collection manually
        distinct_regions = mongo.db.distincts__testdataset.find({
            'value.keys': u'region'
        }).distinct('_id')
        h.assert_equal(sorted(distinct_regions), [u'Region 1', u'Region 2'])

        distincts = logic.entry.distinct('region', dataset_name='testdataset')
        h.assert_equal(sorted(distincts), [u'Region 1', u'Region 2'])

    def test_distincts_create_collection(self):
        testdataset = self._make_dataset(name='testdataset')
        self._make_entry(name='one', region="Region 1", region2="Region 2",
                         dataset=testdataset)
        self._make_entry(name='two', region="Region 2", region2="Region 3",
                         dataset=testdataset)

        h.assert_true('compute_distincts' in mongo.db.system_js.list())

        # compute a distincts collection
        h.assert_true('distincts__testdataset' not in mongo.db.collection_names())

        distincts = logic.entry.distinct('region', dataset_name='testdataset')
        h.assert_true('distincts__testdataset' in mongo.db.collection_names())
        h.assert_equal(sorted(distincts), [u'Region 1', u'Region 2'])

    def test_distinct(self):
        self._make_entry(name='one', region='Region A')
        self._make_entry(name='two', region='Region A')
        self._make_entry(name='three', region='Region B')
        distincts = logic.entry.distinct('region')
        h.assert_equal(distincts, ['Region A', 'Region B'])

    def test_distincts_by_dataset_name(self):
        self._make_entry(name='one', region='Region A')
        self._make_entry(name='two', region='Region A')
        self._make_entry(name='three', region='Region B')
        other_dataset = self._make_dataset('other_dataset')
        self._make_entry(name='four', region='Region C',
                         dataset=other_dataset)

        # without a dataset_name it returns the distincts across all datasets
        distincts = logic.entry.distinct('region')
        h.assert_equal(distincts, ['Region A', 'Region B', 'Region C'])

        # we can limit it with dataset_name
        distincts = logic.entry.distinct('region', dataset_name='other_dataset')
        h.assert_equal(distincts, ['Region C'])

    def test_distincts_with_query_kwarg(self):
        self._make_entry(name='one', region='RegionA')
        self._make_entry(name='two', region='RegionA')
        self._make_entry(name='three', region='RegionB')

        # without a dataset_name it returns the distincts across all datasets
        distincts = logic.entry.distinct('name', region=u'RegionA')
        h.assert_equal(distincts, ['one', 'two'])

    def test_distinct_with_query_kwarg_containing_boolean_value(self):
        self._make_entry(name='one', foo=True)
        self._make_entry(name='two', foo=True)
        self._make_entry(name='three', foo=False)
        distincts = logic.entry.distinct('name', foo=True)
        h.assert_equal(distincts, ['one', 'two'])

    def test_facets(self):
        self._make_entry(name='one', region="Region A")
        self._make_entry(name='two', region="Region A")
        self._make_entry(name='three', region="Region B")
        h.clean_and_reindex_solr()
        facets = logic.entry.facets_for_fields(['name', 'region'])
        h.assert_equal(facets, {u'name': {u'one': 1,
                                          u'two': 1,
                                          u'three': 1},
                                u'region': {'Region A': 2,
                                            'Region B': 1}})

    def test_facets_with_query_kwarg(self):
        self._make_entry(name='one', region="RegionA")
        self._make_entry(name='two', region="RegionA")
        self._make_entry(name='three', region="Region B")
        h.clean_and_reindex_solr()

        facets = logic.entry.facets_for_fields(['name'], region=u'RegionA')
        h.assert_equal(facets, {u'name': {u'one': 1,
                                          u'two': 1}})

    def test_facets_with_query_kwarg_containing_boolean_value(self):
        self._make_entry(name='one', foo=True)
        self._make_entry(name='two', foo=True)
        self._make_entry(name='three', foo=False)
        h.clean_and_reindex_solr()
        facets = logic.entry.facets_for_fields(['name'], foo=True)
        h.assert_equal(facets, {u'name': {u'one': 1,
                                          u'two': 1}})

    def test_facets_with_query_kwarg_and_space(self):
        self._make_entry(name='one', region="Region A")
        self._make_entry(name='two', region="Region A")
        self._make_entry(name='three', region="Region B")
        h.clean_and_reindex_solr()

        facets = logic.entry.facets_for_fields(['name'], region='Region A')

        h.skip("This test has been failing for a long time, commented out. "\
               "Skipping to register known failure that needs fixing eventually.")
        h.assert_equal(facets, {u'name': {u'one': 1,
                                          u'two': 1}})

    def test_facets_by_dataset(self):
        self._make_entry(name='one')
        self._make_entry(name='two')
        other_dataset = self._make_dataset('other_dataset')
        self._make_entry(name='three', dataset=other_dataset)
        self._make_entry(name='four', dataset=other_dataset)
        h.clean_and_reindex_solr()
        # without a dataset_name it returns the distincts across all datasets
        facets = logic.entry.facets_for_fields(['name'])
        h.assert_equal(facets, {u'name': {u'one': 1,
                                          u'two': 1,
                                          u'three': 1,
                                          u'four': 1}})

        # we can limit it with dataset_name
        facets = logic.entry.facets_for_fields(['name'],
                                               dataset_name='other_dataset')

        h.assert_equal(facets, {u'name': {u'three': 1,
                                          u'four': 1}})

    def test_facets_fail_for_solr_textgen_fields(self):
        # facets for a solr field return facets for the tokens stored
        # in the field. Depending on the type this may mean that
        # it's not the string stored in the field, but tokens after
        # splitting, stemming or lowercasing
        self._make_entry(name='one', description="Description One")
        self._make_entry(name='two', description="Description Two")
        h.clean_and_reindex_solr()
        facets = logic.entry.facets_for_fields(['description'])

        # The result is not ["Description One", "Description Two"]
        h.assert_equal(facets, {u'description': {u'description': 2,
                                                   u'two': 1,
                                                   u'one': 1}})

    def test_count(self):
        self._make_entry(name='one')
        self._make_entry(name='two')
        other_dataset = self._make_dataset('other_dataset')
        self._make_entry(name='three', dataset=other_dataset)
        self._make_entry(name='four', dataset=other_dataset)
        h.clean_and_reindex_solr()

        count = logic.entry.count()
        h.assert_equal(count, 4)

    def test_count_with_dataset_name(self):
        self._make_entry(name='one')
        self._make_entry(name='two')
        other_dataset = self._make_dataset('other_dataset')
        self._make_entry(name='three', dataset=other_dataset)
        self._make_entry(name='four', dataset=other_dataset)
        h.clean_and_reindex_solr()

        count = logic.entry.count(dataset_name='other_dataset')
        h.assert_equal(count, 2)

    def test_count_with_query(self):
        self._make_entry(name='one', region="A")
        self._make_entry(name='two', region="A")
        self._make_entry(name='three', region="B")
        self._make_entry(name='four')
        h.clean_and_reindex_solr()

        count = logic.entry.count(region="A")
        h.assert_equal(count, 2)

    def test_count_with_query_kwarg_containing_boolean_value(self):
        self._make_entry(name='one', foo=True)
        self._make_entry(name='two', foo=True)
        self._make_entry(name='three', foo=False)
        h.clean_and_reindex_solr()
        count = logic.entry.count(foo=True)
        h.assert_equal(count, 2)


class TestClassifier(DatabaseTestCase):

    def test_create_classifier(self):
        classifier = logic.classifier.create_classifier(name=u'Test Classifier',
                                                        taxonomy=u'taxonomy')
        h.assert_true(isinstance(classifier, Classifier))

    def test_create_classifier_does_not_delete_attributes_in_existing(self):
        classifier = logic.classifier.create_classifier(u'Test Classifier',
                                                        taxonomy=u'taxonomy',
                                                        extra=u'extra')
        h.assert_true('extra' in classifier)

        upserted_classifier = logic.classifier.create_classifier(u'Test Classifier',
                                                                 taxonomy=u'taxonomy')
        h.assert_true('extra' in upserted_classifier)

    def test_classify_entry(self):
        entry = {'name': u'Test Entry',
                 'amount': 1000.00}
        c_name = u'support-transparency'
        c_taxonomy = u'Good Reasons'
        c_label = u'Support Transparency Initiatives'
        classifier = logic.classifier.create_classifier(name=c_name,
                                                        label=c_label,
                                                        taxonomy=c_taxonomy)
        logic.entry.classify_entry(entry, classifier, name=u'reason')
        h.assert_equal(entry.keys(), [u'reason', 'amount', 'name',
                                        'classifiers'])
        h.assert_equal(entry['classifiers'], [classifier['_id']])
        h.assert_equal(entry['reason']['label'], c_label)
        h.assert_equal(entry['reason']['name'], c_name)
        h.assert_equal(entry['reason']['taxonomy'], c_taxonomy)
        h.assert_true(isinstance(entry['reason']['ref'], DBRef))

    def test_get_classifier(self):
        testname = 'testname'
        testtaxonomy = 'testtaxonomy'
        created = logic.classifier.create_classifier(testname, testtaxonomy)
        fetched = logic.classifier.get_classifier(testname, testtaxonomy)
        h.assert_true(isinstance(fetched, Classifier))
        h.assert_false(created is fetched)
        h.assert_equal(created, fetched)
