from flask import request
from webhelpers import paginate
from urllib import urlencode


def make_url(**args):
    return request.path + '?' + urlencode(args)


class Page(paginate.Page):
    # Overwrite the pager method of the webhelpers.paginate.Page class,
    # so we have our custom layout set as default.

    def __init__(self, *a, **kw):
        super(Page, self).__init__(*a, url=make_url, **kw)

    def pager(self, *args, **kwargs):
        kwargs.update(
            format="<div class='pager'>$link_previous ~2~ $link_next</div>",
            symbol_previous=u'\xab Prev', symbol_next=u'Next \xbb'
        )
        return super(Page, self).pager(*args, **kwargs)
