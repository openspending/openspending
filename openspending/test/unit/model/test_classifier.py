from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

def make_classifier():
    return {
        'name': 'classifier_foo',
        'label': 'Foo Classifier',
        'level': '1',
        'taxonomy': 'class.foo',
        'description': 'Denotes the foo property.',
        'parent': 'class'
    }

class TestClassifier(DatabaseTestCase):

    def test_create(self):
        classifier = model.classifier.create(make_classifier())
        h.assert_equal(classifier['name'], 'classifier_foo')

    def test_create_does_not_delete_attributes_in_existing(self):
        c = make_classifier()
        c['extra'] = 'value'

        classifier = model.classifier.create(c)
        h.assert_equal(classifier['extra'], 'value')

        classifier = model.classifier.create(make_classifier())
        h.assert_equal(classifier['extra'], 'value')
