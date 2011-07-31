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
        _id = model.classifier.create(make_classifier())
        classifier = model.classifier.get(_id)
        h.assert_equal(classifier['name'], 'classifier_foo')

    def test_create_does_not_delete_attributes_in_existing(self):
        c = make_classifier()
        c['extra'] = 'value'

        _id = model.classifier.create(c)
        classifier = model.classifier.get(_id)
        h.assert_equal(classifier['extra'], 'value')

        _id = model.classifier.create(c)
        classifier = model.classifier.get(_id)
        h.assert_equal(classifier['extra'], 'value')
