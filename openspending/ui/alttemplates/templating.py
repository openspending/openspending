from pylons import tmpl_context as c
from pylons import app_globals
from pylons import config

from openspending.ui.lib import helpers as h

from jinja2 import Template, FileSystemLoader
from jinja2.environment import Environment

def render(dirname, filename):
    env = Environment()
    env.loader = FileSystemLoader(dirname)
    template = env.get_template(filename)

    static_cache_version = config.get("openspending.static_cache_version", "")
    if static_cache_version != "":
        static_cache_version = "?" + static_cache_version

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
        "number_symbols_decimal": c.locale.number_symbols.get('decimal'),
        "site_title": app_globals.site_title,
        "static": config.get("openspending.static_path", "/static/"),
        "static_cache_version": static_cache_version
        }
    return template.render(params)
