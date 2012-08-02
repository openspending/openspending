from openspending.model import Dataset, meta as db

from .. import ControllerTestCase, url, helpers as h

class TestEntryController(ControllerTestCase):

    def setup(self):
        super(TestEntryController, self).setup()
        h.load_fixture('cra')
        self.cra = Dataset.by_name('cra')

    def test_view(self):
        t = list(self.cra.entries(limit=1)).pop()
        response = self.app.get(url(controller='entry', action='view',
                                    dataset='cra', id=t['id']))

        assert 'cra' in response

    def test_entry_custom_html(self):
        tpl = '<a href="/custom/path/%s">%s</a>'
        tpl_c = tpl % ('${entry["id"]}', '${entry["name"]}')
        self.cra.entry_custom_html = tpl_c
        db.session.commit()

        t = list(self.cra.entries(limit=1)).pop()

        response = self.app.get(url(controller='entry', action='view',
                                    dataset=self.cra.name,
                                    id=t['id']))

        assert tpl % (t['id'], t['name']) in response, \
               'Custom HTML not present in rendered page!'

    def test_search_assigns_the_query_in_the_tmpl_context(self):
        response = self.app.get(url(controller='entry', action='search', q='the_query'))
        assert 'the_query' == response.tmpl_context.query

