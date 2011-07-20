from decorator import decorator
from pylons.controllers.util import abort
from pylons.i18n import _

def has_role(role, user):
    if user is None: 
        return None
    return role in user.get('_roles', [])

def have_role(role):
    from pylons import tmpl_context as c
    return has_role(role, c.account)

def requires(role):
    def _dec(f, *a, **kw):
        if not have_role(role):
            abort(403, _("You're not authorized to access this page"))
        return f(*a, **kw)
    return decorator(_dec)
