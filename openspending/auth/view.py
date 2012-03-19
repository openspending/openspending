from account import logged_in
from pylons import tmpl_context

import dataset as ds


def create(dataset):
    return ds.read(dataset)


def read(dataset, view):
    return ds.read(dataset)


def update(dataset, view):
    if tmpl_context.account and tmpl_context.account == view.account:
        return True
    return ds.edit(dataset)


def delete(dataset, view):
    return update(dataset, view)
