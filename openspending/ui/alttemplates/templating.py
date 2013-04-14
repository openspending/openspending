import os
from pylons import tmpl_context as c
from pylons import app_globals
from pylons import config

from openspending import auth as can
from openspending.ui.lib import helpers as h

from jinja2 import Template, FileSystemLoader
from jinja2.environment import Environment

import lxml.html
from lxml.html import builder as E

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

def postprocess_forms(s, form_errors):
    def tag_errors(tag, root):
        for i in root.cssselect(tag):
            name = i.attrib.get('name', None)
            value = form_errors.get(name, None)
            if value is not None:
                p = E.P(value)
                p.set('class', 'help-block error')
                i.addnext(p)

    def input_errors(root):
        return tag_errors('input', root)

    def select_errors(root):
        return tag_errors('select', root)

    def textarea_errors(root):
        return tag_errors('textarea', root)

    root = lxml.html.fromstring(s)
    processors = [input_errors, select_errors, textarea_errors]
    [ process(root) for process in processors ]
    return lxml.html.tostring(root)

def render(path, **kwargs):
    """Render a template with jinja2

    Args:
      path (str): the path to the template; should be of the form
      "dir/filename.html"

    """

    env = Environment()
    env.loader = FileSystemLoader(template_rootdir)
    template = env.get_template(path)


    static_cache_version = config.get("openspending.static_cache_version", "")
    if static_cache_version != "":
        static_cache_version = "?" + static_cache_version

    params = {
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
        "h": h,
        "c": c,
        "g": app_globals,
        "can": can,
        "show_rss": hasattr(c, 'show_rss') and c.show_rss or None
        }
    params.update(kwargs)
    form_errors = params.get('form_errors', {})
    return postprocess_forms(template.render(params), form_errors)
