from pylons import tmpl_context


def logged_in():
    return hasattr(
        tmpl_context, 'account') and tmpl_context.account is not None


def create():
    return True


def read(account):
    return True


def update(account):
    return logged_in()


def delete(account):
    return False
