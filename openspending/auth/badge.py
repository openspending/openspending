from flask.ext.login import current_user

from account import logged_in


def create():
    """
    Permission to create a new badge. Only administrators can create badges.
    """
    return logged_in() and current_user.admin


def give(badge, dataset):
    """
    Permission to give a badge to a dataset. Currently only administrators
    can reward datasets with badges.
    """
    return logged_in() and current_user.admin
