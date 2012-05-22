from lxml import html
from urlparse import urljoin
import requests
import os

from pylons import app_globals

class ContentResource(object):

    def __init__(self, section, path):
        self.section = section
        self.path = path
        self.res = None
        self._doc = None

    @property
    def url(self):
        root = app_globals.content_root
        if not root.endswith('/'):
            root = root + '/'
        root += self.section + '/'
        return urljoin(root, self.path)

    @property
    def doc(self):
        if self._doc is None:
            if not self.exists() or not self.is_html():
                return None
            data_res = requests.get(self.url)
            self._doc = html.document_fromstring(data_res.content)
        return self._doc

    def _head(self):
        if self.res is None:
            self.res = requests.head(self.url)
        return self.res

    def exists(self):
        return self._head().ok

    def is_html(self):
        if not self.exists():
            return False
        return self._head().headers.get('content-type') == 'text/html'

    def xpath_inner(self, path):
        if self.doc is None:
            return None
        elem = self.doc.find(path)
        print elem
        if elem is None:
            return None
        elem_strs = map(lambda c: html.tostring(c) + (c.tail or ''),
                        elem.getchildren())
        return (elem.text or '') + '\n'.join(elem_strs)

    @property
    def title(self):
        return self.xpath_inner('.//title')

    @property
    def content(self):
        return self.xpath_inner('.//div[@id="content"]')

    @property
    def html(self):
        return self.xpath_inner('.')

