from openspending import model
from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestEntryController(ControllerTestCase):

    def setup(self):
        super(TestEntryController, self).setup()
        h.load_fixture('cra')
        self.cra = model.Dataset.find_one({'name': 'cra'})

    def test_view(self):
        t = model.entry.find_one()
        response = self.app.get(url(controller='entry', action='view',
                                    id=str(t['_id']), name=t['name']))

        assert 'cra' in response

    def test_view_with_more_entities(self):
        # Test the view for an entry that has
        # entities for more dimensions than to and from
        entry = model.entry.find_one()

        # use the existing 'pog' dimensions and stuff a ref to an entity
        # in there.
        pog_entity = model.Entity(name='pog-entity', label='Test Pog Entity')
        pog_entity.save()
        model.entry.entitify_entry(entry, pog_entity, 'pog')
        model.entry.save(entry)

        response = self.app.get(url(controller='entry', action='view',
                                    id=str(entry['_id']), name=entry['name']))
        assert 'Test Pog Entity' in response

    def test_foi(self):
        t = model.entry.find_one()
        response = self.app.get(url(controller='entry', action='view',
                                    id=str(t['_id']), name=t['name']))

        # For now, just check we AREN'T showing the FOI screen on CRA pages.
        # TODO: more detailed testing.
        assert not 'Make an FOI request' in response

    def test_entry_custom_html(self):
        tpl = '<a href="/custom/path/%s">%s</a>'

        self.cra.entry_custom_html = tpl % ('${entry["_id"]}', '${entry["name"]}')
        self.cra.save()

        t = model.entry.find_one()

        response = self.app.get(url(controller='entry', action='view',
                                    id=str(t['_id']), name=t['name']))

        assert tpl % (t['_id'], t['name']) in response, \
               'Custom HTML not present in rendered page!'

