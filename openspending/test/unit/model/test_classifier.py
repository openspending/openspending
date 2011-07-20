from openspending.model import Classifier
from openspending.test import DatabaseTestCase, helpers as h

def make_classifier():
    return Classifier(name='classifier_foo',
                      label='Foo Classifier',
                      level='1',
                      taxonomy='class.foo',
                      description='Denotes the foo property.',
                      parent='class')

class TestClassifier(DatabaseTestCase):

    def setup(self):
        super(TestClassifier, self).setup()
        self.cla = make_classifier()
        self.cla.save()

    def test_classifier_properties(self):
        h.assert_equal(self.cla.label, 'Foo Classifier')
        h.assert_equal(self.cla.level, '1')
        h.assert_equal(self.cla.taxonomy, 'class.foo')
        h.assert_equal(self.cla.description, 'Denotes the foo property.')
        h.assert_equal(self.cla.parent, 'class')