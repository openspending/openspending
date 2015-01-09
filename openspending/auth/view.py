from flask.ext.login import current_user

from account import logged_in
import dataset as ds


def create(dataset):
    return logged_in() and ds.read(dataset)


def read(dataset, view):
    return ds.read(dataset)


def update(dataset, view):
    if logged_in() and current_user == view.account:
        return True
    return ds.update(dataset)


def delete(dataset, view):
    return update(dataset, view)
