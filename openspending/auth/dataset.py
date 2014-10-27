from account import logged_in
from pylons import tmpl_context


def create():
    return logged_in()


def read(dataset):
    if not dataset.private:
        return True
    return update(dataset)


def update(dataset):
    return logged_in() and (tmpl_context.account.admin or
                            tmpl_context.account in dataset.managers)


def delete(dataset):
    return update(dataset)
