from flask.ext.login import current_user


def logged_in():
    return current_user.is_authenticated()


def is_admin():
    return logged_in() and current_user.admin


def create():
    return True


def read(account):
    return True


def update(account):
    return logged_in()


def delete(account):
    return False
