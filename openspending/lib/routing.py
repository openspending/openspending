from werkzeug.routing import Rule, UnicodeConverter


class FormatConverter(UnicodeConverter):

    def __init__(self, url_map):
        super(FormatConverter, self).__init__(url_map)
        self.regex = '(?:html|json|csv)'


class NoDotConverter(UnicodeConverter):

    def __init__(self, url_map):
        super(NoDotConverter, self).__init__(url_map)
        self.regex = self.regex.replace('/', '/.')


class NamespaceRouteRule(Rule):
    # cf.
    # * http://werkzeug.pocoo.org/docs/0.9/routing/
    # * https://stackoverflow.com/questions/17135006

    def match_compare_key(self):
        #print self.arguments
        return len(self.arguments), -len(self._weights), self._weights
