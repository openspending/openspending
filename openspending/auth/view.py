from account import logged_in
from pylons import tmpl_context

import dataset as ds


def create(dataset):
    return logged_in() and ds.read(dataset)


def read(dataset, view):
    return ds.read(dataset)


def update(dataset, view):
    if logged_in() and tmpl_context.account == view.account:
        return True
    return ds.update(dataset)


def delete(dataset, view):
    return update(dataset, view)
