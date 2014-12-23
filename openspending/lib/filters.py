from lxml import html
import babel.numbers
from flask.ext.babel import get_locale
from webhelpers.html import literal
from webhelpers.markdown import markdown as _markdown
from webhelpers.text import truncate


def markdown(*args, **kwargs):
    return literal(_markdown(*args, **kwargs))


def markdown_preview(text, length=150):
    if not text:
        return ''
    try:
        md = html.fromstring(unicode(markdown(text)))
        text = md.text_content()
    except:
        pass
    if length:
        text = truncate(text, length=length, whole_word=True)
    return text.replace('\n', ' ')


def format_currency(amount, dataset, locale=None):
    """ Wrapper around babel's format_currency which fetches the currency
    from the dataset. Uses the current locale to format the number. """
    try:
        if amount is None:
            return "-"
        if amount == 'NaN':
            return "-"
        locale = locale or get_locale()
        currency = 'USD'
        if dataset is not None and dataset.currency is not None:
            currency = dataset.currency
        return babel.numbers.format_currency(int(amount), currency, locale=locale)
    except:
        return amount


def entry_description(entry):
    fragments = []
    if 'from' in entry and 'to' in entry:
        fragments.extend([
            entry.get('from').get('label'),
            entry.get('to').get('label')
        ])
    if isinstance(entry.get('description'), basestring):
        fragments.append(entry.get('description'))
    else:
        for k, v in entry.items():
            if k in ['from', 'to', 'taxonomy', 'html_url']:
                continue
            if isinstance(v, dict):
                fragments.append(v.get('label'))
            elif isinstance(v, basestring):
                fragments.append(v)
    description = " - ".join(fragments)
    return markdown_preview(description)


def readable_url(url):
    if len(url) > 55:
        return url[:15] + " .. " + url[len(url) - 25:]
    return url


def render_value(value):
    if isinstance(value, dict):
        return value.get('label', value.get('name', value))
    return value
