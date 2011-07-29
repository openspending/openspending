from bson.dbref import DBRef

from openspending import logic
from openspending import mongo
from openspending import model
from openspending.model import Classifier, Dataset
from openspending.test import DatabaseTestCase, helpers as h

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
        model.entry.classify_entry(entry, classifier, name=u'reason')
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
