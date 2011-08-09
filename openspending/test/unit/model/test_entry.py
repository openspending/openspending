from openspending import mongo
from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

def make_dataset(name='testdataset'):
    dataset = model.dataset.find_one_by('name', name)
    return dataset if dataset else model.dataset.create({'name': name})

def make_entry(name='testentry', region='testregion', amount=1.0,
               dataset=None, **kwargs):
    if dataset is None:
        dataset = make_dataset()

    entry = model.entry.create(dict(name=name, region=region,
                                    amount=amount, **kwargs),
                               dataset)
    return entry


class TestEntry(DatabaseTestCase):

    def setup(self):
        h.skip_if_stubbed_solr()
        super(TestEntry, self).setup()

    def test_distincts(self):
        testdataset = make_dataset(name='testdataset')
        make_entry(name='one', region="Region 1", region2="Region 2",
                   dataset=testdataset)
        make_entry(name='two', region="Region 2", region2="Region 3",
                   dataset=testdataset)

        # compute a distincts collection
        mongo.db.system_js.compute_distincts('testdataset')
        h.assert_true('distincts__testdataset' in mongo.db.collection_names())

        # test the distincts collection manually
        coll = mongo.db.distincts__testdataset
        distinct_regions = coll.find({'value.keys': 'region'}).distinct('_id')
        h.assert_equal(sorted(distinct_regions), [u'Region 1', u'Region 2'])

        distincts = model.entry.distinct('region', dataset_name='testdataset')
        h.assert_equal(sorted(distincts), [u'Region 1', u'Region 2'])

    def test_distincts_create_collection(self):
        testdataset = make_dataset(name='testdataset')
        make_entry(name='one', region="Region 1", region2="Region 2",
                   dataset=testdataset)
        make_entry(name='two', region="Region 2", region2="Region 3",
                   dataset=testdataset)

        # compute a distincts collection
        h.assert_true('distincts__testdataset' not in mongo.db.collection_names())

        distincts = model.entry.distinct('region', dataset_name='testdataset')
        h.assert_true('distincts__testdataset' in mongo.db.collection_names())
        h.assert_equal(sorted(distincts), [u'Region 1', u'Region 2'])

    def test_distinct(self):
        make_entry(name='one', region='Region A')
        make_entry(name='two', region='Region A')
        make_entry(name='three', region='Region B')
        distincts = model.entry.distinct('region')
        h.assert_equal(distincts, ['Region A', 'Region B'])

    def test_distincts_by_dataset_name(self):
        make_entry(name='one', region='Region A')
        make_entry(name='two', region='Region A')
        make_entry(name='three', region='Region B')
        other_dataset = make_dataset('other_dataset')
        make_entry(name='four', region='Region C', dataset=other_dataset)

        # without a dataset_name it returns the distincts across all datasets
        distincts = model.entry.distinct('region')
        h.assert_equal(distincts, ['Region A', 'Region B', 'Region C'])

        # we can limit it with dataset_name
        distincts = model.entry.distinct('region', dataset_name='other_dataset')
        h.assert_equal(distincts, ['Region C'])

    def test_distincts_with_query_kwarg(self):
        make_entry(name='one', region='RegionA')
        make_entry(name='two', region='RegionA')
        make_entry(name='three', region='RegionB')

        # without a dataset_name it returns the distincts across all datasets
        distincts = model.entry.distinct('name', region=u'RegionA')
        h.assert_equal(distincts, ['one', 'two'])

    def test_distinct_with_query_kwarg_containing_boolean_value(self):
        make_entry(name='one', foo=True)
        make_entry(name='two', foo=True)
        make_entry(name='three', foo=False)
        distincts = model.entry.distinct('name', foo=True)
        h.assert_equal(distincts, ['one', 'two'])

    def test_classify_entry(self):
        entry = {
            'name': 'Test Entry',
            'amount': 1000.00
        }
        classifier = {
            '_id': 123,
            'name': 'support-transparency',
            'taxonomy': 'Good Reasons',
            'label': 'Support Transparency Initiatives'
        }

        model.entry.classify_entry(entry, classifier, name='reason')
        h.assert_equal(entry.keys(), ['reason', 'amount', 'name', 'classifiers'])
        h.assert_equal(entry['classifiers'], [classifier['_id']])
        h.assert_equal(entry['reason']['label'], 'Support Transparency Initiatives')
        h.assert_equal(entry['reason']['name'], 'support-transparency')
        h.assert_equal(entry['reason']['taxonomy'], 'Good Reasons')
        h.assert_true(isinstance(entry['reason']['ref'], mongo.DBRef))