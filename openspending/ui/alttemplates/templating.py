import os
from pylons import tmpl_context as c
from pylons import app_globals
from pylons import config

from openspending.ui.lib import helpers as h

from jinja2 import Template, FileSystemLoader
from jinja2.environment import Environment

template_rootdir = "openspending/ui/alttemplates"

def languages(detected_languages, current_language):
    def lang_triple(lang):
        return {
            "lang_code": lang[0], 
            "lang_name": lang[1], 
            "current_locale" : {
                True: "current_locale",
                False: ""
                }[ current_language == lang[0] ]
            }
    return [ lang_triple(l) for l in detected_languages ]

def section_active(section):
    sections = [ "blog", "dataset", "search", "resources", "help", "about" ]
    tmp = dict([ (s, section == s)for s in sections ])
    tmp["dataset"] = bool(c.dataset)

    return dict([ (k, {
                True: "active",
                False: ""
                }[v]) for k,v in tmp.iteritems() ])

def render(bare_dirname, filename):
    dirname = os.path.join(template_rootdir, bare_dirname)
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
        "static_cache_version": static_cache_version,
        "messages": list(h._flash.pop_messages()),
        "languages": languages(c.detected_l10n_languages, c.language),
        "section_active": section_active(c.content_section),
        "account": c.account is not None,
        "h": h
        }
    return template.render(params)
