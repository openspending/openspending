from pymongo.cursor import Cursor
from webhelpers import paginate
from webhelpers.paginate import get_wrapper as _get_wrapper

class _SolrResultWrapper(object):
    def __init__(self, result):
        self.result = result
        
    def __getitem__(self, i):
        return self.result.get('response', {}).get('docs', [])
        
    def __len__(self):
        return self.result.get('response', {}).get('numFound', 0)

class _MongoCursorWrapper(object):
    def __init__(self, cur):
        self.cur = cur
        
    def __getitem__(self, r):
        cur = self.cur.clone()
        if r.start: 
            cur.skip(r.start)
        if r.stop: 
            cur.limit(r.stop - r.start if r.start else r.stop)
        return list(cur)
        
    def __len__(self):
        return self.cur.clone().count()
    

def get_wrapper(obj, sqlalchemy_session=None):
    if isinstance(obj, Cursor):
        return _MongoCursorWrapper(obj)
    if isinstance(obj, dict) and 'responseHeader' in obj:
        return _SolrResultWrapper(obj)
    return _get_wrapper(obj, sqlalchemy_session=sqlalchemy_session)
    
paginate.get_wrapper = get_wrapper

class Page(paginate.Page):
    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.
    def pager(self, *args, **kwargs):
        kwargs.update(
            format="<div class='pager'>$link_previous ~2~ $link_next</div>",
            symbol_previous=u'\xab Prev', symbol_next=u'Next \xbb'
        )
        return super(Page, self).pager(*args, **kwargs)
