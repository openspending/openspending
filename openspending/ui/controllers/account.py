from pylons import config

import logging

import colander

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from repoze.who.api import get_api

from openspending import model
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
        if config.get('openspending.sandbox_mode') == 'true':
            default_roles = ["user", "admin"]
        else:
            default_roles = ["user"]

        errors, values = {}, None
        if request.method == 'POST':
            try:
                schema = Register()
                values = request.params
                account = schema.deserialize(values)
                exists = model.Account.find_one({"name": account['name']})
                if exists:
                    raise colander.Invalid(
                        Register.name,
                        _("Login name already exists, please choose a "
                          "different one"))
                if not account['password1'] == account['password2']:
                    raise colander.Invalid(Register.password1, _("Passwords \
                        don't match!"))
                password = account['password1']
                account['password_hash'] = \
                    generate_password_hash(password)
                del account['password1']
                del account['password2']
                account['_roles'] = default_roles
                model.Account.c.insert(account)
                who_api = get_api(request.environ)
                authenticated, headers = who_api.login(
                    {"login": account['name'], "password": password})
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
                model.Account.c.update({"name": c.account_name},
                                       {"$set": data})
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
