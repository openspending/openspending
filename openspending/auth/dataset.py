from account import logged_in
from pylons import tmpl_context

def create():
    return logged_in()

def read(dataset):
    if not dataset.private:
        return True
    return update(dataset)

def update(dataset):
    if logged_in():
        if tmpl_context.account.admin:
            return True
        elif tmpl_context.account in dataset.managers:
            return True
    return False

def delete(dataset):
    if logged_in():
        if tmpl_context.account.admin:
            return True
        elif tmpl_context.account in dataset.managers:
            return True
    return False

def list_changes():
    return logged_in() and tmpl_context.account.admin
