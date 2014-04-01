from lxml import html
from urlparse import urljoin
import requests

from pylons import app_globals


class ContentResource(object):

    def __init__(self, section, path, headers=None):
        self.section = section
        self.path = path
        self.res = None
        self._doc = None

        # Set the headers so that sites that require accept and user-agent
        # for spam protection can also be used
        if headers is None:
            # Defaults for the user agent and accept
            self.headers = {'User-Agent': 'OpenSpending in-site browser',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        else:
            self.headers = headers

    @property
    def url(self):
        root = app_globals.content_root
        if not root.endswith('/'):
            root += '/'
        root += self.section + '/'
        return urljoin(root, self.path)

    @property
    def doc(self):
        if self._doc is None:
            if not self.exists() or not self.is_html():
                return None
            # Get the content of the web site
            data_res = requests.get(self.url, headers=self.headers)
            content = data_res.content.decode('utf-8')
            self._doc = html.document_fromstring(content)
        return self._doc

    def _head(self):
        if self.res is None:
            # Get the head for the page
            self.res = requests.head(self.url, headers=self.headers)
        return self.res

    def exists(self):
        return self._head().ok

    def is_html(self):
        """
        A function that checks whether the content type is text/html
        since we need it to be html in order to parse it
        """

        # The header must be ok (the site must exist)
        if not self.exists():
            return False

        # Is text/html a part of the content-type?
        return 'text/html' in self._head().headers.get('content-type')

    def xpath_inner(self, path):
        if self.doc is None:
            return None
        elem = self.doc.find(path)
        if elem is None:
            return None
        elem_strs = map(lambda c: html.tostring(c) + (c.tail or ''),
                        elem.getchildren())
        text = (elem.text or '') + '\n'.join(elem_strs)
        text = text.decode('utf-8')
        return text

    @property
    def title(self):
        return self.xpath_inner('.//title')

    @property
    def content(self):
        return self.xpath_inner('.//div[@id="content"]')

    @property
    def html(self):
        return self.xpath_inner('.')
