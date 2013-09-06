from openspending.lib import json
from openspending.lib import solr_util as solr
from openspending.model import Dataset, Account

from .. import ControllerTestCase, url, helpers as h

class TestApiController(ControllerTestCase):
    def setup(self):
        super(TestApiController, self).setup()
        h.load_fixture('cra')
    
    def test_aggregate(self):
        response = self.app.get(url(controller='api',
                                    action='aggregate',
                                    dataset='cra'))
        assert '"metadata": {' in response, response
        assert '"dataset": "cra"' in response, response
        assert '"include": []' in response, response
        assert '"dates":' in response, response
        assert '"axes": []' in response, response
        assert '"results": [' in response

    def test_aggregate_with_breakdown(self):
        u = url(controller='api', action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response

    def test_jsonp_aggregate(self):
        # Copied from test_aggregate_with_breakdown.
        callback = randomjsonpcallback()
        u = url(controller='api',
            callback=callback, action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response
        assert valid_jsonp(response, callback)

    def test_aggregate_with_per_region(self):
        u = url(controller='api', action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
            'per-population2006': 'region'
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response
        assert '0.1' in response, response

    ## Dropped support for this.
    #def test_aggregate_with_per_time(self):
    #    u = url(controller='api', action='aggregate', **{
    #        'dataset': 'cra',
    #        'per-gdp_deflator2006': ''
    #    })
    #    response = self.app.get(u)
    #    assert '"axes": []' in response, response
    #    assert '"2006"' in response, response
    #    assert '18445770.0' in response, response

    def test_mytax(self):
        u = url(controller='api', action='mytax', income=20000)
        response = self.app.get(u)
        assert '"tax": ' in response, response
        assert '"explanation": ' in response, response
        # TODO: check amounts still work.

    def test_jsonp_mytax(self):
        # Copied from test_mytax.
        callback = randomjsonpcallback()
        u = url(controller='api', action='mytax', income=20000,
          callback=callback)
        response = self.app.get(u)
        assert '"tax": ' in response, response
        assert '"explanation": ' in response, response
        assert valid_jsonp(response, callback)


def randomjsonpcallback(prefix='cb'):
    """Generate a random identifier suitable, beginning with *prefix*,
    for using as a JSONP callback name."""

    import random
    import string
    return prefix + ''.join(random.choice(string.letters) for
      _ in range(6))


def valid_jsonp(response, callback):
    """True if *response* is valid JSONP using *callback* as the
    callback name.  Currently does not completely validate
    everything."""

    return (
        ((callback + '(') in response, response) and
        (str(response)[-2:] == ');' or str(response)[-1] == ')')
    )

class TestApiNewDataset(ControllerTestCase):
    def setup(self):
        super(TestApiNewDataset, self).setup()
        self.user = h.make_account('test_new')
        self.user.api_key = 'd0610659-627b-4403-8b7f-6e2820ebc95d'
        self.user.secret_api_key = 'be33f8a7-c0f0-46f1-8d8d-e0e094866099'

        self.user2 = h.make_account('test_new2')
        self.user2.api_key = 'c011c340-8dad-419c-8138-1c6ded86ead5'
        self.user2.secret_api_key = '488c1775-7426-4f02-8a47-e287b0d62aec'

    def test_01_correct_operation(self):
        user = Account.by_name('test_new')
        assert user.api_key == 'd0610659-627b-4403-8b7f-6e2820ebc95d'
        assert user.secret_api_key == 'be33f8a7-c0f0-46f1-8d8d-e0e094866099'

        u = url(controller='api', action='new', **{
            'metadata':'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'apikey':'d0610659-627b-4403-8b7f-6e2820ebc95d',
            'signature':'566f9ca6df2a5e004d1ad80a2e83a982'
        })
        response = self.app.post(u)
        Dataset.by_name('openspending-example').private = False
        assert "200" in response.status
        assert Dataset.by_name('openspending-example')

    def test_new_02_no_signature(self):
        u = url(controller='api', action='new', **{
            'metadata':'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'apikey':'037020d2-ab08-4d53-b6c3-c890510d92fb'
        })
        response = self.app.post(u, expect_errors=True)
        assert "400" in response.status
        assert not Dataset.by_name('openspending-example')

    def test_new_03_wrong_signature(self):
        u = url(controller='api', action='new', **{
            'metadata':'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'apikey':'037020d2-ab08-4d53-b6c3-c890510d92fb',
            'signature':'566f9ca6df2a5e004d1ad80a2e83a981'
        })
        response = self.app.post(u, expect_errors=True)
        assert "400" in response.status
        assert not Dataset.by_name('openspending-example')

    def test_new_04_no_right_user(self):
        # First we add a Dataset with user 'test_new'
        user = Account.by_name('test_new')
        assert user.api_key == 'd0610659-627b-4403-8b7f-6e2820ebc95d'
        assert user.secret_api_key == 'be33f8a7-c0f0-46f1-8d8d-e0e094866099'

        u = url(controller='api', action='new', **{
            'metadata':'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'apikey':'d0610659-627b-4403-8b7f-6e2820ebc95d',
            'signature':'566f9ca6df2a5e004d1ad80a2e83a982'
        })
        response = self.app.post(u)
        Dataset.by_name('openspending-example').private = False
        assert "200" in response.status
        assert Dataset.by_name('openspending-example')

        # After that we try to update the Dataset with user 'test_new2'
        user = Account.by_name('test_new2')
        assert user.api_key == 'c011c340-8dad-419c-8138-1c6ded86ead5'
        assert user.secret_api_key == '488c1775-7426-4f02-8a47-e287b0d62aec'
        
        u2 = url(controller='api', action='new', **{
            'metadata':'https://dl.dropbox.com/u/3250791/sample-openspending-model.json',
            'csv_file':'http://mk.ucant.org/info/data/sample-openspending-dataset.csv',
            'apikey':'c011c340-8dad-419c-8138-1c6ded86ead5',
            'signature':'1ba8b0483eaae060750dc6729b249e65'
        })

        response2 = self.app.post(u2, expect_errors=True)
        assert '403' in response2.status        


class TestApiSearch(ControllerTestCase):

    def setup(self):

        super(TestApiSearch, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_search_01_no_query(self):
        response = self.app.get(url(controller='api', action='search'))
        out = json.loads(str(response.body))['response']
        assert out['numFound'] == 36, out['numFound']
        assert out['docs'][0]['dataset'] == 'cra', out

    def test_search_02_query(self):
        response = self.app.get(url(controller='api', action='search',
                                    q='Children'))
        out = json.loads(str(response.body))['response']
        assert out['numFound'] == 7, out['numFound']
        exp_entity = 'Department for Children, Schools and Families'
        print out['docs'][0]
        assert out['docs'][0]['from.label_facet'] == exp_entity, out['docs'][0]

    def test_search_03_jsonpify(self):
        callback = 'mycallback'
        response = self.app.get(url(controller='api', action='search',
                                    q='children', callback=callback))
        assert response.body.startswith('%s({"responseHeader"'
                                        % callback), response.body

    def test_search_04_invalid_query(self):
        response = self.app.get(url(controller='api', action='search',
                                    q='time:'), expect_errors=True)
        assert "400" in response.status, response.status



    
