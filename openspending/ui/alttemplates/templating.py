from pylons import tmpl_context as c
from openspending.ui.lib import helpers as h

from jinja2 import Template, FileSystemLoader
from jinja2.environment import Environment

def render(dirname, filename):
    env = Environment()
    env.loader = FileSystemLoader(dirname)
    template = env.get_template(filename)

    params = {
        "dataset_label": c.dataset.label,
        "dimensions": c.dataset.dimensions,
        "dataset_name": c.dataset.name,
        "language": c.language,
        "script_root": h.script_root(),
        "script_boot": h.script_tag('prod/boot'),
        "bootstrap_css": h.static('style/bootstrap.css'),
        "style_css": h.static('style/style.css'),
        "number_symbols_group": c.locale.number_symbols.get('group'),
        "number_symbols_decimal": c.locale.number_symbols.get('decimal')
        }
    return template.render(params)
