from pylons.i18n import _, add_fallback, get_lang, set_lang, gettext
from pylons import config
from babel import Locale

import os
import babel
import gettext

import logging
log = logging.getLogger(__name__)

def get_available_languages():
    # Magic paths copied from pylons.i18n.translation._get_translator
    localedir = os.path.join(config['pylons.paths']['root'], 'i18n')
    messagefiles = gettext.find(config['pylons.package'], localedir,
                                languages=babel.Locale('en').languages.keys(),
                                all=True)
    return [path.split('/')[-3] for path in messagefiles]

def get_available_locales():
    return map(Locale.parse, get_available_languages())

def get_language_pairs():
    languages = get_available_languages()
    langlist = zip(languages, 
                   [Locale.parse(lang).display_name for lang in languages])
    # Filter out bogus language codes before they screw us over completely
    # (Hint: 'no' is not a real language code)
    return filter(lambda (language, name): name is not None, langlist)

def get_default_locale():
    from pylons import config
    return Locale.parse(config.get('lang')) or \
            Locale.parse('en')

def set_session_locale(locale):
    assert locale in get_available_languages()
    from pylons import session
    session['locale'] = locale
    session.save()

def handle_request(request, tmpl_context):
    from pylons import session

    tmpl_context.language = locale = None
    if 'locale' in session:
        locale = Locale.parse(session.get('locale'))
    else:
        requested = [l.replace('-', '_') for l in request.languages]
        locale = Locale.parse(Locale.negotiate(get_available_languages(), requested))

    if locale is None:
        locale = get_default_locale()
    
    options = [str(locale), locale.language, str(get_default_locale()),
        get_default_locale().language]
    for language in options:
        try:
            set_lang(language)
            # Lose the territory part of the locale string
            tmpl_context.language = get_lang()[0].split('_')[0]
            break
        except: pass
