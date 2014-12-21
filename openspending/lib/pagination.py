from webhelpers import paginate


class Page(paginate.Page):
    # Overwrite the pager method of the webhelpers.paginate.Page class,
    # so we have our custom layout set as default.

    def pager(self, *args, **kwargs):
        kwargs.update(
            format="<div class='pager'>$link_previous ~2~ $link_next</div>",
            symbol_previous=u'\xab Prev', symbol_next=u'Next \xbb'
        )
        return super(Page, self).pager(*args, **kwargs)
