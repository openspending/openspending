from openspending.ui.test import ControllerTestCase, url, helpers as h

class TestEntityController(ControllerTestCase):
    '''mixed unit and functional tests for EntityController'''

    def _make_one(self, name, **kwargs):
        from openspending.model import Entity
        entity = kwargs
        entity['name'] = name
        new_id = Entity.c.save(entity, manipulate=True)
        return Entity.find_one({'_id': new_id})

    def test_404_with_name(self):
        from webob.exc import HTTPNotFound
        from openspending.ui.controllers.entity import EntityController
        entity = self._make_one(name='Test Entity')
        controller = EntityController()
        h.assert_raises(HTTPNotFound, controller.view,
                          id=entity['name'], slug='dontcare')

    def test_404_with_wrong_objectid(self):
        from bson import ObjectId
        from webob.exc import HTTPNotFound
        from openspending.ui.controllers.entity import EntityController
        entity = self._make_one(name='Test Entity')
        controller = EntityController()
        other_objectid = ObjectId()
        h.assert_not_equal(entity['_id'], other_objectid)
        h.assert_raises(HTTPNotFound, controller.view,
                          id=str(other_objectid), slug='dontcare')

    def test_302_with_wrong_slug(self):
        from webob.exc import HTTPMovedPermanently
        from openspending.ui.controllers.entity import EntityController
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
        h.assert_equal(response._headers['Content-Type'], 'application/json')
        h.assert_true('"name": "Test Entity",' in response._body,
                        'json fragment not found. got: %s' % response._body)

    def test_browser_for_entity(self):
        h.skip_if_stubbed_solr()

        from openspending import model

        dataset = model.Dataset(name='testdataset')
        dataset.save()
        dataset_ref_dict = dataset.to_ref_dict()

        entity = self._make_one(name="Test Entity", label="Test Entity Label")
        entity_ref_dict = entity.to_ref_dict()

        entry = {'name': 'Test Entry',
                 'label': 'Test Entry Label',
                 'from': entity_ref_dict,
                 'to': entity_ref_dict,
                 'amount': 10.0,
                 'dataset': dataset_ref_dict}
        _id = model.entry.create(entry)

        h.clean_and_reindex_solr()

        entity_url = url(controller='entity', id=str(entity['_id']),
                         slug='test-entity-label', action='view')
        response = self.app.get(entity_url)

        h.assert_equal(response._status, '200 OK')
        h.assert_true('<b>1 entries</b> found.<br />' in response)
        h.assert_true('entries.json">' in response)
        h.assert_true('entries.csv">' in response)
