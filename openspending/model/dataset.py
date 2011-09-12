from genshi.template import TextTemplate

from . import base

collection = 'dataset'

base.init_model_module(__name__, collection)

# dataset objects probably have the following fields
#   _id
#   name
#   label
#   description
#   currency
#   entry_custom_html

def render_entry_custom_html(doc, entry):
    """Render dataset ``doc``'s custom html for entry ``entry``"""
    custom_html = doc.get('entry_custom_html')
    if custom_html:
        return _render_custom_html(custom_html, 'entry', entry)
    else:
        return None

def _render_custom_html(tpl, name, obj):
    if tpl:
        tpl = TextTemplate(tpl)

        ctx = {name: obj}
        stream = tpl.generate(**ctx)
        return stream.render()
    else:
        return None