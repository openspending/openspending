from ordereddict import OrderedDict
import hashlib

from openspending import model
from openspending.reference.category import CATEGORIES
from openspending.reference.country import COUNTRIES
from openspending.reference.language import LANGUAGES


class ParamParser(object):
    defaults = OrderedDict()
    defaults['page'] = 1
    defaults['pagesize'] = 10000
    defaults['order'] = None

    def __init__(self, params):
        self.params = self.defaults.copy()
        self.params.update(params)

    def parse(self):
        self._output = {}
        self._errors = []

        for key in self.params.keys():
            if key not in self.defaults:
                continue

            parser = 'parse_{0}'.format(key)
            if hasattr(self, parser):
                result = getattr(self, parser)(self.params[key])
            else:
                result = self.params[key]

            if result is not None:
                self._output[key] = result

        return self._output, self._errors

    def key(self):
        params = sorted(self.params.items())
        return hashlib.sha1(repr(params)).hexdigest()

    def _error(self, msg):
        self._errors.append(msg)

    def parse_page(self, page):
        return max(1, self._to_float('page', page))

    def parse_pagesize(self, pagesize):
        return self._to_int('pagesize', pagesize)

    def parse_order(self, order):
        if not order:
            return []

        result = []
        for part in order.split('|'):
            try:
                dimension, direction = part.split(':')
            except ValueError:
                self._error('Wrong format for "order". It has to be '
                            'specified with request parameters in the form '
                            '"order=dimension:direction|dimension:direction". '
                            'We got: "order=%s"' % order)
                return
            else:
                if direction not in ('asc', 'desc'):
                    self._error('Order direction can be "asc" or "desc". We '
                                'got "%s" in "order=%s"' %
                                (direction, order))
                    return

                if direction == 'asc':
                    reverse = False
                else:
                    reverse = True

                result.append((dimension, reverse))
        return result

    def _to_float(self, name, value):
        try:
            return float(value)
        except ValueError:
            self._error('"%s" has to be a number, it is: %s' %
                       (name, value))

    def _to_int(self, name, value):
        try:
            return int(value)
        except ValueError:
            self._error('"%s" has to be an integer, it is: %s' %
                       (name, value))

    def _to_bool(self, value): 
        if value.lower().strip() in ['true', '1', 'yes', 'on']:
            return True
        return False

class DatasetIndexParamParser(ParamParser):
    """
    Parameter parser for the dataset index page (which is served
    differently based on languages, territories and category chosen.
    """

    # We cannot use the defaults from ParamParser since that includes
    # order.
    defaults = OrderedDict()
    defaults['languages'] = []
    defaults['territories'] = []
    defaults['category'] = None
    # Used for pagination in html pages only
    defaults['page'] = 1
    defaults['pagesize'] = 25

    def __init__(self, params):
        """
        Initialize dataset index parameter parser, and make
        the initial params available as part of the instance
        """
        self.request_params = params
        super(DatasetIndexParamParser, self).__init__(params)

    def parse_languages(self, language):
        """
        Get the languages. This ignores the language supplied since multiple
        languages can be provided with multiple parameters and ParamParser
        does not support that.
        """
        # We force the language codes to lowercase and strip whitespace
        languages = [l.lower().strip() \
                         for l in self.request_params.getall('languages')]
        # Check if this language is supported by OpenSpending
        # If not we add an error
        for lang in languages:
            if lang.lower().strip() not in LANGUAGES:
                self._error('Language %s not found' % lang)

        return languages

    def parse_territories(self, territory):
        """
        Get the territories. This ignores the territory supplied since multiple
        territories can be provided with multiple parameters and ParamParser
        does not support that.
        """
        # We force the territory codes to uppercase and strip whitespace
        # Isn't it great that we're so consistent with uppercase and lowercase
        # (uppercase here, lowercase in languages and categories)
        territories = [t.upper().strip() \
                           for t in self.request_params.getall('territories')]

        # Check if this territory is supported by OpenSpending
        # If not we add an error
        for country in territories:
            if country not in COUNTRIES:
                self._error('Territory %s not found' % country)

        return territories

    def parse_category(self, category):
        """
        Get the category and check if it exists in
        supported categories. If so we return it.
        """
        if category:
            # We want the category to be lowercase and stripped of whitespace
            category = category.lower().strip()
            # Check if category is supported, if not add an error
            if category in CATEGORIES:
                return category
            else:
                self._error('Category %s not found' % category)

        # We return None if there's an error of no category
        return None

class AggregateParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['dataset'] = None
    defaults['drilldown'] = None
    defaults['cut'] = None
    defaults['order'] = None
    defaults['inflate'] = None
    defaults['format'] = 'json'
    defaults['measure'] = 'amount'

    def parse_dataset(self, dataset_name):
        if not dataset_name:
            self._error('dataset name not provided')
            return

        dataset = model.Dataset.by_name(dataset_name)
        if dataset is None:
            self._error('no dataset with name "%s"' % dataset_name)
            return

        return dataset

    def parse_drilldown(self, drilldown):
        if not drilldown:
            return []
        return drilldown.split('|')

    def parse_format(self, format):
        format = format.lower().strip()
        if not format or not format in ('json', 'csv'):
            return 'json'
        return format

    def parse_cut(self, cuts):
        if not cuts:
            return []

        result = []
        for cut in cuts.split('|'):
            try:
                dimension, value = cut.split(':')
            except ValueError:
                self._error('Wrong format for "cut". It has to be specified '
                            'with request cut_parameters in the form '
                            '"cut=dimension:value|dimension:value". '
                            'We got: "cut=%s"' %
                            cuts)
                return
            else:
                result.append((dimension, value))
        return result

    def parse_measure(self, measures):
        """
        Parse the measure parameter which can be either a single measure or
        multiple measures separated by a pipe ('|'). The parser also checks
        to see if the measure is in fact a measure in the dataset model.

        Returns a list of measures even if it is only a single measure.
        Returns None if noe dataset or measure is not in the dataset's model
        (along with an error).
        """

        # Get the dataset which should already have been parsed
        if self._output.get('dataset') is None:
            return

        # Get a list of all measurement names for the given dataset
        measure_names = [m.name for m in self._output['dataset'].measures]

        result = []

        # Split the measures on | and check if it is in dataset if so append
        # it to our results, if not raise and error and return None
        for measure in measures.split('|'):
            if measure not in measure_names:
                self._error('no measure with name "%s"' % measure)
                return

            result.append(measure)

        return result

class SearchParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['q'] = ''
    defaults['filter'] = None
    defaults['category'] = None
    defaults['dataset'] = None
    defaults['page'] = 1
    defaults['stats'] = 'false'
    defaults['pagesize'] = 100
    defaults['order'] = None
    defaults['facet_field'] = None
    defaults['facet_page'] = 1
    defaults['facet_pagesize'] = 100
    defaults['expand_facet_dimensions'] = None
    defaults['format'] = 'json'

    MAX_FACET_PAGESIZE = 100

    def parse_filter(self, filter):
        if not filter:
            return {}

        filters = {}
        for f in filter.split('|'):
            try:
                key, value = f.split(':')
            except ValueError:
                self._error('Wrong format for "filter". It has to be '
                            'specified with request parameters in the form '
                            '"filter=key1:value1|key2:value2". '
                            'We got: "filter=%s"' % filter)
                break
            else:
                filters[key] = value

        return filters

    def parse_format(self, format):
        format = format.lower().strip()
        if not format or not format in ('json', 'csv'):
            return 'json'
        return format

    def parse_dataset(self, dataset):
        datasets = []

        if dataset:
            for name in dataset.split('|'):
                dataset = model.Dataset.by_name(name)
                if dataset is None:
                    self._error('no dataset with name "%s"' % name)
                    return
                datasets.append(dataset)
        return datasets

    def parse_pagesize(self, pagesize):
        return self._to_int('pagesize', pagesize)

    def parse_category(self, category):
        category = category.lower().strip() if category else None
        if category in CATEGORIES:
            return category
        return None

    def parse_facet_field(self, facet_field):
        if not facet_field:
            return

        return facet_field.split('|')

    def parse_facet_page(self, page):
        return max(1, self._to_float('facet_page', page))

    def parse_stats(self, stats):
        return self._to_bool(stats)

    def parse_facet_pagesize(self, pagesize):
        return min(self.MAX_FACET_PAGESIZE, self._to_int('facet_pagesize', pagesize))

    def parse_expand_facet_dimensions(self, expand_facet_dimensions):
        return expand_facet_dimensions is not None


class DistinctParamParser(ParamParser):
    defaults = ParamParser.defaults.copy()
    defaults['q'] = ''
    defaults['page'] = 1
    defaults['pagesize'] = 100

    def __init__(self, params):
        self.params = self.defaults.copy()
        self.params.update(params)

    def parse_pagesize(self, pagesize):
        return min(100, self._to_int('pagesize', pagesize))


class DistinctFieldParamParser(DistinctParamParser):
    defaults = DistinctParamParser.defaults.copy()
    defaults['attribute'] = None

    def __init__(self, dimension, params):
        self.dimension = dimension
        super(DistinctFieldParamParser, self).__init__(params)

    def parse_attribute(self, attribute):
        if not isinstance(self.dimension, model.CompoundDimension):
            return self.dimension
        try:
            return self.dimension[attribute]
        except KeyError:
            return self.dimension['label']
