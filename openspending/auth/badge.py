from account import logged_in
from pylons import tmpl_context


def create():
    """
    Permission to create a new badge. Only administrators can create badges.
    """
    return logged_in() and tmpl_context.account.admin


def give(badge, dataset):
    """
    Permission to give a badge to a dataset. Currently only administrators
    can reward datasets with badges.
    """
    return logged_in() and tmpl_context.account.admin
