"""
Common validation checks within the model.
"""
import re

RESERVED_TERMS = ['entry', 'entries', 'dataset', 'datasets', 'dimension',
                  'dimensions', 'editor', 'meta', 'id', 'login', 'logout',
                  'settings', 'browser', 'explorer', 'member', 'register',
                  'after_login', 'after_logout', 'locale', 'reporterror',
                  'getinvolved', 'api', '500', 'error']

def chained(*validators):
    """ 
    Chain a list of predicates and raise an error on the first 
    failure. This means only the first error is shown, so it 
    makes sense to pass in predicates from the more general to 
    the more specific.
    """
    def _validator(value):
        for validator in validators:
            res = validator(value)
            if res is not True:
                return res
        return True
    return _validator

def reserved_name(name):
    """ These are names that have a special meaning in URLs and
    cannot be used for dataset or dimension names. """
    if name.lower() in RESERVED_TERMS:
        return "'%s' is a reserved word and cannot be used here" % name
    return True

def database_name(name):
    if not re.match(r"^[\w\-\_]+$", name):
        return ("Name must include only "
                "letters, numbers, dashes and underscores")
    return True

def nonempty_string(text):
    if not isinstance(text, basestring):
        return "Must be text, not %s" % type(text)
    if not len(text.strip()):
        return "Must have at least one non-whitespace character."
    return True
