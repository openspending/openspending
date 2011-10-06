from ... import DatabaseTestCase, helpers as h

from openspending import model
from openspending.ui.lib.views import View

class TestViews(DatabaseTestCase):
    def setup(self):
        super(TestViews, self).setup()
        h.load_fixture('cra')
        self.dataset = model.Dataset.by_name('cra')

    def get_view(self, name='test_view', **kwargs):

        kwargs.update(dataset=self.dataset,
                      name=name,
                      label="A label",
                      dimension="from")

        return View(**kwargs)

    def test_create_view(self):
        view = self.get_view("test_create_view")

        h.assert_equal(view.dataset, self.dataset)
        h.assert_equal(view.name, "test_create_view")

    def test_apply_view(self):
        view = self.get_view("test_apply_view")

        view.apply_to(model.entry, {"region": u'ENGLAND_South West'})

        soc = model.entry.find_one({"region": u'ENGLAND_South West'})

        v = soc['views']['test_apply_view']
        h.assert_equal(v['label'], view.label)

        not_soc = model.entry.find_one({"region": {"$ne": u'ENGLAND_South West'}})

        assert not 'views' in not_soc or not_soc.get('views').get('test0') is None

    def test_by_name(self):
        view = self.get_view("test1", cuts={"foo": "Hello"})
        view.apply_to(model.entry, {'region': u'ENGLAND_South West'})

        soc = model.entry.find_one({'region': u'ENGLAND_South West'})

        loaded = View.by_name(soc, 'test1')
        h.assert_equal(loaded.label, view.label)
        h.assert_equal(loaded.cuts, view.cuts)

        h.assert_raises(ValueError, View.by_name, soc, 'not-there')

    def test_dimensions(self):
        view = self.get_view("test_dimensions", cuts={"label": "Hello"})

        assert len(view.base_dimensions) == 3
        assert "label" in view.base_dimensions, view.base_dimensions
        assert "from" in view.base_dimensions, view.base_dimensions
        assert "year" in view.base_dimensions, view.base_dimensions

        view = self.get_view("test_dimensions_2", dimension="from", drilldown="hello")

        assert "hello" in view.full_dimensions, view.full_dimensions
        assert "hello" not in view.base_dimensions, view.base_dimensions
        assert len(view.full_dimensions) == 3
