import csv
import json
from StringIO import StringIO

from pylons import cache as pylons_cache

from bson import ObjectId
from webob.exc import HTTPNotFound, HTTPMovedPermanently

from openspending import model
from openspending.ui.controllers.entity import EntityController

from .. import ControllerTestCase, url, helpers as h

class TestEntityController(ControllerTestCase):

    def setup(self):
        super(TestEntityController, self).setup()
        h.load_fixture('cra')
        self.ent = model.entity.find_one_by('name', 'Dept063')

    def _make_one(self, name, **kwargs):
        entity = kwargs
        entity['name'] = name
        return model.entity.create(entity)

    def test_view_noslug(self):
        # Should respond with 301 to URL with slug
        self.app.get(url(controller='entity', action='view',
                         id=self.ent['_id'], status=301))

    def test_view(self):
        h.skip_if_stubbed_solr()
        response = self.app.get(url(controller='entity', action='view',
                                    id=self.ent['_id']))
        response = response.follow() # expect one redirect
        h.assert_true('Department for Innovation, Universities and Skills' in response,
                      "'Department for Innovation, Universities and Skills' not in response!")

    def test_view_not_objectid(self):
        ent = model.entity.create({'_id': 'foobar',
                                   'name': 'foobar',
                                   'label': 'Foo Bar'})
        response = self.app.get(url(controller='entity', action='view',
                                    id='foobar', format='json'))
        obj = json.loads(response.body)
        h.assert_true('Foo Bar' in response,
                      "'Foo Bar' not in response!")

    def test_view_json(self):
        response = self.app.get(url(controller='entity', action='view',
                                    id=self.ent['_id'], format='json'))
        obj = json.loads(response.body)
        h.assert_equal(obj['label'], 'Department for Innovation, Universities and Skills')

    def test_view_csv(self):
        response = self.app.get(url(controller='entity', action='view',
                                    id=self.ent['_id'], format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        h.assert_equal(len(obj), 1)
        h.assert_equal(obj[0]['label'], 'Department for Innovation, Universities and Skills')

    def test_entries(self):
        h.skip_if_stubbed_solr()
        dius = model.entity.find_one_by('name', 'Dept063')
        response = self.app.get(url(controller='entity', action='entries',
                                    id=self.ent['_id']))

    def test_entries_json(self):
        h.skip_if_stubbed_solr()
        dius = model.entity.find_one_by('name', 'Dept063')
        response = self.app.get(url(controller='entity', action='entries',
                                    id=self.ent['_id'], format='json'))
        obj = json.loads(response.body)
        # TODO: test some content rather than simply asserting 200

    def test_entries_csv(self):
        h.skip_if_stubbed_solr()
        dius = model.entity.find_one_by('name', 'Dept063')
        response = self.app.get(url(controller='entity', action='entries',
                                    id=self.ent['_id'], format='csv'))
        r = csv.DictReader(StringIO(response.body))
        obj = [l for l in r]
        # TODO: test some content rather than simply asserting 200

    def test_404_with_name(self):
        entity = self._make_one(name='Test Entity')
        controller = EntityController()
        h.assert_raises(HTTPNotFound, controller.view,
                        id=entity['name'], slug='dontcare')

    def test_404_with_wrong_objectid(self):
        entity = self._make_one(name='Test Entity')
        controller = EntityController()
        other_objectid = ObjectId()
        h.assert_not_equal(entity['_id'], other_objectid)
        h.assert_raises(HTTPNotFound, controller.view,
                        id=str(other_objectid), slug='dontcare')

    def test_302_with_wrong_slug(self):
        entity = self._make_one(name='Test Entity')
        controller = EntityController()
        h.assert_raises(HTTPMovedPermanently, controller.view,
                        id=str(entity['_id']), slug='wrong-slug')

    def test_common_pageview(self):
        h.skip_if_stubbed_solr()

        entity = self._make_one(name="Test Entity", label="Test Entity Label")
        response = self.app.get(url(controller='entity',
                                    id=str(entity['_id']),
                                    slug='test-entity-label',
                                    action='view'))

        h.assert_equal(response._status, '200 OK')
        h.assert_true('Test Entity Label' in response)
        json_name = '%s.json' % entity['_id']
        h.assert_true(json_name in response,
                      'Entity json "%s" not found in output' % json_name)

    def test_entity_as_json(self):
        entity = self._make_one(name="Test Entity", label="Test Entity Label")
        response = self.app.get(url(controller='entity',
                                    id=str(entity['_id']),
                                    action='view',
                                    format='json'))
        h.assert_equal(response._status, '200 OK')
        h.assert_equal(response.headers['Content-Type'], 'application/json')
        h.assert_true('"name": "Test Entity",' in response.body,
                      'json fragment not found. got: %s' % response.body)

    def test_browser_for_entity(self):
        h.skip_if_stubbed_solr()

        dataset = model.dataset.create({'name': 'testdataset'})

        entity = self._make_one(name="Test Entity", label="Test Entity Label")
        entity_ref_dict = model.entity.get_ref_dict(entity)

        entry = model.entry.create({'name': 'Test Entry',
                                    'label': 'Test Entry Label',
                                    'from': entity_ref_dict,
                                    'to': entity_ref_dict,
                                    'amount': 10.0},
                                   dataset)

        h.clean_and_reindex_solr()

        entity_url = url(controller='entity', id=str(entity['_id']),
                         slug='test-entity-label', action='view')
        response = self.app.get(entity_url)

        h.assert_equal(response.status, '200 OK')
        h.assert_true('<b>1 entries</b> found.<br />' in response)
        h.assert_true('entries.json">' in response)
        h.assert_true('entries.csv">' in response)
