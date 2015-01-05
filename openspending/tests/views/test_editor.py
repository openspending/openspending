import json

from flask import url_for

from openspending.tests.base import ControllerTestCase
from openspending.tests.helpers import make_account, load_fixture
from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.model.source import Source


class TestEditorController(ControllerTestCase):

    def setUp(self):
        super(TestEditorController, self).setUp()
        self.user = make_account('test')
        load_fixture('cra', self.user)

    def test_overview(self):
        response = self.client.get(url_for('editor.index', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'Manage the dataset' in response.data

    def test_core_edit_mask(self):
        response = self.client.get(url_for('editor.core_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'EUR' in response.data
        assert 'Update' in response.data

    def test_core_update(self):
        self.client.post(url_for('editor.core_update', dataset='cra'),
                         data={'name': 'cra', 'label': 'Common Rough Act',
                               'description': 'I\'m a banana',
                               'currency': 'EUR', 'languages': 'en',
                               'territories': 'gb',
                               'category': 'budget', 'default_time': 2009},
                         query_string={'api_key': self.user.api_key})
        cra = Dataset.by_name('cra')
        assert cra.label == 'Common Rough Act', cra.label
        assert cra.currency == 'EUR', cra.currency

    def test_core_update_invalid_category(self):
        response = self.client.post(url_for('editor.core_update', dataset='cra'),
                                    data={'name': 'cra',
                                          'label': 'Common Rough Act',
                                          'description': 'I\'m a banana',
                                          'currency': 'EUR', 'languages': 'en',
                                          'territories': 'gb',
                                          'category': 'foo',
                                          'default_time': 2009},
                                    query_string={'api_key': self.user.api_key})
        assert 'valid category' in response.data
        cra = Dataset.by_name('cra')
        assert cra.label != 'Common Rough Act', cra.label

    def test_core_update_invalid_label(self):
        response = self.client.post(url_for('editor.core_update', dataset='cra'),
                                    data={'name': 'cra', 'label': '',
                                          'description': 'I\'m a banana',
                                          'currency': 'GBP'},
                                    query_string={'api_key': self.user.api_key})
        assert 'Required' in response.data
        cra = Dataset.by_name('cra')
        assert cra.label != '', cra.label

    def test_core_update_invalid_language(self):
        response = self.client.post(url_for('editor.core_update', dataset='cra'),
                                    data={'name': 'cra', 'label': 'CRA',
                                          'languages': 'esperanto',
                                          'description': 'I\'m a banana',
                                          'currency': 'GBP',
                                          'default_time': 2009},
                                    query_string={'api_key': self.user.api_key})
        assert 'updated' not in response.data
        cra = Dataset.by_name('cra')
        assert 'esperanto' not in cra.languages

    def test_core_update_invalid_territory(self):
        response = self.client.post(url_for('editor.core_update', dataset='cra'),
                                    data={'name': 'cra', 'label': 'CRA',
                                          'territories': 'su',
                                          'description': 'I\'m a banana',
                                          'currency': 'GBP',
                                          'default_time': 2009},
                                    query_string={'api_key': self.user.api_key})
        assert 'updated' not in response.data
        cra = Dataset.by_name('cra')
        assert 'su' not in cra.territories

    def test_core_update_invalid_currency(self):
        response = self.client.post(url_for('editor.core_update', dataset='cra'),
                                    data={'name': 'cra',
                                          'label': 'Common Rough Act',
                                          'description': 'I\'m a banana',
                                          'currency': 'glass pearls',
                                          'default_time': 2009},
                                    query_string={'api_key': self.user.api_key})
        assert 'not a valid currency' in response.data
        cra = Dataset.by_name('cra')
        assert cra.currency == 'GBP', cra.label

    def test_dimensions_edit_mask(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.init()
        cra.generate()
        src = Source(cra, self.user, 'file:///dev/null')
        src.analysis = {'columns': ['amount', 'etc']}
        db.session.add(src)
        db.session.commit()
        response = self.client.get(url_for('editor.dimensions_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert '"amount"' in response.data
        assert 'Update' in response.data

    def test_dimensions_edit_mask_with_data(self):
        cra = Dataset.by_name('cra')
        src = Source(cra, self.user, 'file:///dev/null')
        src.analysis = {'columns': ['amount', 'etc']}
        db.session.add(src)
        db.session.commit()
        response = self.client.get(url_for('editor.dimensions_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'cannot edit dimensions' in response.data
        assert '"amount"' not in response.data
        assert 'Update' not in response.data

    def test_dimensions_update_invalid_json(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.init()
        cra.generate()
        response = self.client.post(url_for('editor.dimensions_update', dataset='cra'),
                                    data={'mapping': 'banana'},
                                    query_string={'api_key': self.user.api_key})
        assert '400' in response.status, response.status

    def test_dimensions_update_valid_json(self):
        cra = Dataset.by_name('cra')
        cra.drop()
        cra.init()
        cra.generate()
        response = self.client.post(url_for('editor.dimensions_update', dataset='cra'),
                                    data={'mapping': """{
                                                          "amount": {
                                                            "column": "IMPORTE PEF",
                                                            "datatype": "float",
                                                            "default_value": "",
                                                            "description": null,
                                                            "label": "Amount",
                                                            "type": "measure"
                                                          },
                                                          "theid": {
                                                            "attributes": {
                                                              "label": {
                                                                "column": "FF",
                                                                "datatype": "string",
                                                                "default_value": ""
                                                              },
                                                              "name": {
                                                                "column": "id",
                                                                "datatype": "id",
                                                                "default_value": ""
                                                              }
                                                            },
                                                            "description": null,
                                                            "key": true,
                                                            "label": "Theid",
                                                            "type": "compound"
                                                          },
                                                          "time": {
                                                            "column": "DATE",
                                                            "datatype": "date",
                                                            "default_value": "",
                                                            "description": null,
                                                            "format": null,
                                                            "label": "Time",
                                                            "type": "date"
                                                          }
                                                        }"""},
                                    query_string={'api_key': self.user.api_key})
        assert '200' in response.status, response.status

    def test_views_edit_mask(self):
        response = self.client.get(url_for('editor.views_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert '"default"' in response.data
        assert 'Update' in response.data

    def test_views_update(self):
        cra = Dataset.by_name('cra')
        views = cra.data['views']
        views[0]['label'] = 'Banana'
        response = self.client.post(url_for('editor.views_update', dataset='cra'),
                                    data={'views': json.dumps(views)},
                                    query_string={'api_key': self.user.api_key})
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert 'Banana' in repr(cra.data['views'])

    def test_views_update_invalid_json(self):
        response = self.client.post(url_for('editor.views_update', dataset='cra'),
                                    data={'views': 'banana'},
                                    query_string={'api_key': self.user.api_key})
        assert '400' in response.status, response.status

    def test_team_edit_mask(self):
        response = self.client.get(url_for('editor.team_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'Add someone' in response.data
        assert 'Save' in response.data

    def test_team_update(self):
        response = self.client.post(url_for('editor.team_update', dataset='cra'),
                                    data={},
                                    query_string={'api_key': self.user.api_key})
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert len(cra.managers.all()) == 1, cra.managers

    def test_templates_edit_mask(self):
        response = self.client.get(url_for('editor.templates_edit', dataset='cra'),
                                   query_string={'api_key': self.user.api_key})
        assert 'Update' in response.data

    def test_templates_update(self):
        response = self.client.post(url_for('editor.templates_update', dataset='cra'),
                                    data={'serp_title': 'BANANA'},
                                    query_string={'api_key': self.user.api_key})
        assert '200' in response.status, response.status
        cra = Dataset.by_name('cra')
        assert cra.serp_title == 'BANANA', cra.serp_title

    def test_drop(self):
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)
        # double-check authz
        response = self.client.post(url_for('editor.drop', dataset='cra'))
        assert '403' in response.status
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)

        response = self.client.post(url_for('editor.drop', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        cra = Dataset.by_name('cra')
        assert len(cra) == 0, len(cra)

    def test_delete(self):
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)
        # double-check authz
        response = self.client.post(url_for('editor.delete', dataset='cra'))
        assert '403' in response.status
        cra = Dataset.by_name('cra')
        assert len(cra) == 36, len(cra)

        response = self.client.post(url_for('editor.delete', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        cra = Dataset.by_name('cra')
        assert cra is None, cra

    def test_publish(self):
        cra = Dataset.by_name('cra')
        cra.private = True
        db.session.commit()
        response = self.client.post(url_for('editor.publish', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        cra = Dataset.by_name('cra')
        assert cra.private is False, cra.private
        response = self.client.post(url_for('editor.publish', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        assert '400' in response.status, response.status

    def test_retract(self):
        cra = Dataset.by_name('cra')
        assert cra.private is False, cra.private
        response = self.client.post(url_for('editor.retract', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        cra = Dataset.by_name('cra')
        assert cra.private is True, cra.private
        response = self.client.post(url_for('editor.retract', dataset='cra'),
                                    query_string={'api_key': self.user.api_key})
        assert '400' in response.status, response.status
