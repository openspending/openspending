import os
import babel
import gettext
import logging

from flask import session, request
from babel import Locale

log = logging.getLogger(__name__)


def get_available_languages():
    localedir = os.path.dirname(__file__)
    messagefiles = gettext.find('openspending.ui', localedir,
                                languages=babel.Locale('en').languages.keys(),
                                all=True)
    return [path.split(os.path.sep)[-3] for path in messagefiles]


def get_available_locales():
    return map(Locale.parse, get_available_languages())


def get_language_pairs():
    languages = get_available_languages()
    langlist = zip(languages,
                   [Locale.parse(lang).display_name for lang in languages])
    # Filter out bogus language codes before they screw us over completely
    # (Hint: 'no' is not a real language code)
    return filter(lambda language_name: language_name[1] is not None, langlist)


def set_session_locale(locale):
    session['locale'] = locale
    session.modified = True


def get_locale():
    if 'locale' in session:
        name = session.get('locale')
    else:
        requested = request.accept_languages.values()
        requested = [l.replace('-', '_') for l in requested]
        name = Locale.negotiate(get_available_languages(), requested)

    return Locale.parse(name)
