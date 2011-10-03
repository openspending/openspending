from webhelpers import paginate
from webhelpers.paginate import get_wrapper as _get_wrapper

class _SolrResultWrapper(object):
    def __init__(self, result):
        self.result = result
        
    def __getitem__(self, i):
        return self.result.get('response', {}).get('docs', [])
        
    def __len__(self):
        return self.result.get('response', {}).get('numFound', 0)

def get_wrapper(obj, sqlalchemy_session=None):
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
