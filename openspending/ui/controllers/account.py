from pylons import config

import logging

import colander

from pylons import app_globals, request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from repoze.who.api import get_api

from openspending.model import account
from openspending.ui.lib.account import Register, Settings
from openspending.ui.lib import helpers as h
from openspending.ui.lib.authz import requires
from openspending.ui.lib.base import BaseController, render
from openspending.ui.lib.security import generate_password_hash

log = logging.getLogger(__name__)

class AccountController(BaseController):

    def login(self):
        return render('account/login.html')

    def register(self):
        if app_globals.sandbox_mode:
            default_roles = ["user", "admin"]
        else:
            default_roles = ["user"]

        errors, values = {}, None
        if request.method == 'POST':
            try:
                schema = Register()
                values = request.params
                acc = schema.deserialize(values)
                exists = account.find_one_by('name', acc['name'])
                if exists:
                    raise colander.Invalid(
                        Register.name,
                        _("Login name already exists, please choose a "
                          "different one"))
                if not acc['password1'] == acc['password2']:
                    raise colander.Invalid(Register.password1, _("Passwords \
                        don't match!"))
                password = acc['password1']
                acc['password_hash'] = generate_password_hash(password)
                del acc['password1']
                del acc['password2']
                acc['roles'] = default_roles
                account.create(acc)
                who_api = get_api(request.environ)
                authenticated, headers = who_api.login({
                    "login": acc['name'],
                    "password": password
                })
                response.headers.extend(headers)
                return redirect("/")
            except colander.Invalid, i:
                errors = i.asdict()
        return render('account/login.html', form_fill=values,
                form_errors=errors)

    @requires("user")
    def settings(self):
        errors, values = {}, c.account
        if request.method == 'POST':
            try:
                schema = Settings()
                values = request.params
                data = schema.deserialize(values)
                if not data['password1'] == data['password2']:
                    raise colander.Invalid(Register.password1,
                                           _("Passwords don't match!"))

                if len(data['password1']):
                    password = data['password1']
                    data['password_hash'] = generate_password_hash(password)
                del data['password1']
                del data['password2']
                account.update(c.account, {"$set": data})
                h.flash_success(_("Your settings have been updated."))
            except colander.Invalid, i:
                errors = i.asdict()
        return render('account/settings.html', form_fill=values,
                form_errors=errors)

    def after_login(self):
        if c.account is not None:
            h.flash_success(_("Welcome back, %s!") % c.account.get("name"))
            redirect("/")
        else:
            h.flash_error(_("Incorrect user name or password!"))
            redirect("/login")

    def after_logout(self):
        h.flash_success(_("You have been logged out."))
        redirect("/")
