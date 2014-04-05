from openspending.tests.base import DatabaseTestCase
from openspending.tests import helpers as h

from openspending import model
from openspending.ui.lib.views import View


class TestViews(DatabaseTestCase):

    def setup(self):
        super(TestViews, self).setup()
        h.load_fixture('cra')
        self.dataset = model.Dataset.by_name('cra')

    def get_view(self, name='default', **kwargs):
        return View(self.dataset, kwargs)

    def test_by_name(self):
        assert len(self.dataset.data['views']) == 4

        default = View.by_name(self.dataset, self.dataset, 'default')
        assert default is not None, default
        assert default.entity == 'dataset', default.entity
        assert default.name == 'default', default.name
        assert View.by_name(self.dataset, self.dataset, 'region')

        cf = {'taxonomy': 'cofog'}
        cfa = View.by_name(self.dataset, cf, 'default', 'cofog1')
        assert cfa, cfa
        assert cfa.dimension == 'cofog1', cfa.dimension

        h.assert_raises(ValueError, View.by_name, self.dataset,
                        cfa, 'not-there')
