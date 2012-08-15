from ... import TestCase, helpers as h

from openspending.lib.paramparser import ParamParser, AggregateParamParser, SearchParamParser


class TestParamParser(TestCase):
    def test_defaults(self):
        out, err = ParamParser({}).parse()
        h.assert_equal(out['page'], 1)
        h.assert_equal(out['pagesize'], 10000)
        h.assert_equal(out['order'], [])

    def test_page(self):
        out, err = ParamParser({'page': 'foo'}).parse()
        h.assert_equal(len(err), 1)
        h.assert_true('"page" has to be a number' in err[0])

    def test_page_fractional(self):
        out, err = ParamParser({'page': '1.2'}).parse()
        h.assert_equal(out['page'], 1.2)
        out, err = ParamParser({'page': '0.2'}).parse()
        h.assert_equal(out['page'], 1)

    def test_pagesize(self):
        out, err = ParamParser({'pagesize': 'foo'}).parse()
        h.assert_equal(len(err), 1)
        h.assert_true('"pagesize" has to be an integer' in err[0])

    def test_order(self):
        out, err = ParamParser({'order': 'foo:asc|amount:desc'}).parse()
        h.assert_equal(out['order'], [('foo', False), ('amount', True)])

        out, err = ParamParser({'order': 'foo'}).parse()
        h.assert_true('Wrong format for "order"' in err[0])

        out, err = ParamParser({'order': 'foo:boop'}).parse()
        h.assert_true('Order direction can be "asc" or "desc"' in err[0])

class TestAggregateParamParser(TestCase):
    def test_defaults(self):
        out, err = AggregateParamParser({}).parse()
        h.assert_equal(out['page'], 1)
        h.assert_equal(out['pagesize'], 10000)
        h.assert_equal(err[0], 'dataset name not provided')

    @h.patch('openspending.lib.paramparser.model.Dataset')
    def test_dataset(self, model_mock):
        ds = h.Mock()
        ds.measures = []
        model_mock.by_name.return_value = ds

        out, err = AggregateParamParser({'dataset': 'foo'}).parse()
        h.assert_equal(out['dataset'], ds)

    def test_drilldown(self):
        out, err = AggregateParamParser({'drilldown': 'foo|bar|baz'}).parse()
        h.assert_equal(out['drilldown'], ['foo', 'bar', 'baz'])

    def test_format(self):
        out, err = AggregateParamParser({'format': 'json'}).parse()
        h.assert_equal(out['format'], 'json')

        out, err = AggregateParamParser({'format': 'csv'}).parse()
        h.assert_equal(out['format'], 'csv')

        out, err = AggregateParamParser({'format': 'html'}).parse()
        h.assert_equal(out['format'], 'json')

    @h.patch('openspending.lib.paramparser.model.Dataset')
    def test_cut(self, model_mock):
        ds = h.Mock()
        ds.measures = []
        model_mock.by_name.return_value = ds

        out, err = AggregateParamParser({'dataset': 'foo', 'cut': 'foo:one|bar:two'}).parse()
        h.assert_equal(out['cut'], [('foo', 'one'), ('bar', 'two')])

        out, err = AggregateParamParser({'dataset': 'foo', 'cut': 'foo:one|bar'}).parse()
        h.assert_true('Wrong format for "cut"' in err[0])

    @h.patch('openspending.lib.paramparser.model.Dataset')
    def test_measure(self, model_mock):
        ds = h.Mock()
        amt = h.Mock()
        amt.name = 'amount'
        bar = h.Mock()
        bar.name = 'bar'
        ds.measures = [amt, bar]
        model_mock.by_name.return_value = ds

        out, err = AggregateParamParser({'dataset': 'foo'}).parse()
        h.assert_equal(out['measure'], 'amount')

        out, err = AggregateParamParser({'dataset': 'foo', 'measure': 'bar'}).parse()
        h.assert_equal(out['measure'], 'bar')

        out, err = AggregateParamParser({'dataset': 'foo', 'measure': 'baz'}).parse()
        h.assert_true('no measure with name "baz"' in err[0])


class TestSearchParamParser(TestCase):

    def test_filter(self):
        out, err = SearchParamParser({'filter': 'foo:one|bar:two'}).parse()
        h.assert_equal(out['filter'], {'foo': 'one', 'bar': 'two'})

        out, err = SearchParamParser({'filter': 'foo:one|bar'}).parse()
        h.assert_true('Wrong format for "filter"' in err[0])

    @h.patch('openspending.lib.paramparser.model.Dataset')
    def test_dataset(self, model_mock):
        def _mock_dataset(name):
            if name == 'baz':
                return None
            ds = h.Mock()
            ds.name = name
            return ds

        model_mock.by_name.side_effect = _mock_dataset

        out, err = SearchParamParser({'dataset': 'foo|bar'}).parse()
        h.assert_equal([x.name for x in out['dataset']], ['foo', 'bar'])

        out, err = SearchParamParser({'dataset': 'baz'}).parse()
        h.assert_true('no dataset with name "baz"' in err[0])

    def test_pagesize(self):
        out, err = SearchParamParser({'pagesize': '73'}).parse()
        h.assert_equal(out['pagesize'], 73)

        out, err = SearchParamParser({'pagesize': '140'}).parse()
        h.assert_equal(out['pagesize'], 100)

    def test_facet_field(self):
        out, err = SearchParamParser({'facet_field': 'foo|bar|baz'}).parse()
        h.assert_equal(out['facet_field'], ['foo', 'bar', 'baz'])

    def test_category(self):
        out, err = SearchParamParser({'category': 'banana'}).parse()
        h.assert_equal('category' in out, False)
        out, err = SearchParamParser({'category': 'spending'}).parse()
        h.assert_equal(out['category'], 'spending')

    def test_facet_page(self):
        out, err = SearchParamParser({'facet_page': '14'}).parse()
        h.assert_equal(out['facet_page'], 14)

    def test_facet_page_fractional(self):
        out, err = SearchParamParser({'facet_page': '1.7'}).parse()
        h.assert_equal(out['facet_page'], 1.7)
        out, err = SearchParamParser({'facet_page': '0.6'}).parse()
        h.assert_equal(out['facet_page'], 1)

    def test_facet_pagesize(self):
        out, err = SearchParamParser({'facet_pagesize': '73'}).parse()
        h.assert_equal(out['facet_pagesize'], 73)

        out, err = SearchParamParser({'facet_pagesize': '140'}).parse()
        h.assert_equal(out['facet_pagesize'], 100)

    def test_expand_facet_dimensions(self):
        out, err = SearchParamParser({}).parse()
        h.assert_equal(out['expand_facet_dimensions'], False)

        out, err = SearchParamParser({'expand_facet_dimensions': ''}).parse()
        h.assert_equal(out['expand_facet_dimensions'], True)
