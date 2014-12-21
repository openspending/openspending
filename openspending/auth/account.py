from flask.ext.login import current_user


def logged_in():
    return current_user.is_authenticated()


def create():
    return True


def read(account):
    return True


def update(account):
    return logged_in()


def delete(account):
    return False
