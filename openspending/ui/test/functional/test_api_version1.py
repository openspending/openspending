from openspending.lib import json

from .. import ControllerTestCase, url, helpers as h

class TestApiController(ControllerTestCase):
    def setup(self):
        super(TestApiController, self).setup()
        h.load_fixture('cra')
    
    def test_aggregate(self):
        response = self.app.get(url(controller='api/version1',
                                    action='aggregate',
                                    dataset='cra'))
        assert '"metadata": {' in response, response
        assert '"dataset": "cra"' in response, response
        assert '"include": []' in response, response
        assert '"dates":' in response, response
        assert '"axes": []' in response, response
        assert '"results": [' in response

    def test_aggregate_with_breakdown(self):
        u = url(controller='api/version1', action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response

    def test_jsonp_aggregate(self):
        # Copied from test_aggregate_with_breakdown.
        callback = randomjsonpcallback()
        u = url(controller='api/version1',
            callback=callback, action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response
        assert valid_jsonp(response, callback)

    def test_aggregate_with_per_region(self):
        u = url(controller='api/version1', action='aggregate', **{
            'dataset': 'cra',
            'breakdown-region': 'yes',
            'per-population2006': 'region'
        })
        response = self.app.get(u)
        assert '"region"' in response, response
        assert '"ENGLAND_London"' in response, response
        assert '0.1' in response, response

    def test_mytax(self):
        u = url(controller='api/version1', action='mytax', income=20000)
        response = self.app.get(u)
        assert '"tax": ' in response, response
        assert '"explanation": ' in response, response
        # TODO: check amounts still work.

    def test_jsonp_mytax(self):
        # Copied from test_mytax.
        callback = randomjsonpcallback()
        u = url(controller='api/version1', action='mytax', income=20000,
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

class TestApiSearch(ControllerTestCase):

    def setup(self):

        super(TestApiSearch, self).setup()
        h.load_fixture('cra')
        h.clean_and_reindex_solr()

    def test_search_01_no_query(self):
        response = self.app.get(url(controller='api/version1', action='search'))
        out = json.loads(str(response.body))['response']
        assert out['numFound'] == 36, out['numFound']
        assert out['docs'][0]['dataset'] == 'cra', out

    def test_search_02_query(self):
        response = self.app.get(url(controller='api/version1', action='search',
                                    q='Children'))
        out = json.loads(str(response.body))['response']
        assert out['numFound'] == 7, out['numFound']
        exp_entity = 'Department for Children, Schools and Families'
        print out['docs'][0]
        assert out['docs'][0]['from.label_facet'] == exp_entity, out['docs'][0]

    def test_search_03_jsonpify(self):
        callback = 'mycallback'
        response = self.app.get(url(controller='api/version1', action='search',
                                    q='children', callback=callback))
        assert response.body.startswith('%s({"responseHeader"'
                                        % callback), response.body

    def test_search_04_invalid_query(self):
        response = self.app.get(url(controller='api/version1', action='search',
                                    q='time:'), expect_errors=True)
        assert "400" in response.status, response.status



    
