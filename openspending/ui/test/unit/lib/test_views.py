from ... import DatabaseTestCase, helpers as h

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
        assert len(self.dataset.data['views'])==4

        default = View.by_name(self.dataset, self.dataset, 'default')
        assert default is not None, default
        assert default.entity=='dataset', default.entity
        assert default.name=='default', default.name
        assert View.by_name(self.dataset, self.dataset, 'region')

        cf = {'taxonomy': 'cofog'}
        cfa = View.by_name(self.dataset, cf, 'default', 'cofog1')
        assert cfa, cfa
        assert cfa.dimension=='cofog1', cfa.dimension

        h.assert_raises(ValueError, View.by_name, self.dataset, 
                cfa, 'not-there')

    def test_dimensions(self):
        view = self.get_view("default", entity='entity',
                dimension='from',
                cuts={"label": "Hello"})

        assert len(view.base_dimensions) == 3
        assert not None in view.base_dimensions, view.base_dimensions
        assert "label" in view.base_dimensions, view.base_dimensions
        assert "from" in view.base_dimensions, view.base_dimensions
        assert "year" in view.base_dimensions, view.base_dimensions

        view = self.get_view("default", entity='entity',
                dimension="from", drilldown="hello")

        assert "hello" in view.full_dimensions, view.full_dimensions
        assert "hello" not in view.base_dimensions, view.base_dimensions
        assert len(view.full_dimensions) == 3
