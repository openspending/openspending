from lxml import html
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
