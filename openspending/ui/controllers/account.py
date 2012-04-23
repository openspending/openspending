from pylons import config

import logging

import colander

from pylons import app_globals, request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from repoze.who.api import get_api

from openspending.model import meta as db
from openspending.model.account import Account, AccountRegister, \
    AccountSettings
from openspending.lib.paramparser import DistinctParamParser
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render, require
from openspending.ui.lib.security import generate_password_hash
from openspending.lib.jsonexport import to_jsonp

log = logging.getLogger(__name__)


class AccountController(BaseController):

    def login(self):
        return render('account/login.html')

    def register(self):
        require.account.create()
        errors, values = {}, None
        if request.method == 'POST':
            try:
                schema = AccountRegister()
                values = request.params
                data = schema.deserialize(values)
                if Account.by_name(data['name']):
                    raise colander.Invalid(
                        AccountRegister.name,
                        _("Login name already exists, please choose a "
                          "different one"))
                if not data['password1'] == data['password2']:
                    raise colander.Invalid(AccountRegister.password1,
                                           _("Passwords don't match!"))
                account = Account()
                account.name = data['name']
                account.fullname = data['fullname']
                account.email = data['email']
                account.password = generate_password_hash(data['password1'])
                db.session.add(account)
                db.session.commit()
                who_api = get_api(request.environ)
                authenticated, headers = who_api.login({
                    "login": account.name,
                    "password": data['password1']
                })
                response.headers.extend(headers)
                return redirect("/")
            except colander.Invalid, i:
                errors = i.asdict()
        return render('account/login.html', form_fill=values,
                form_errors=errors)

    def settings(self):
        require.account.update(c.account)
        errors, values = {}, c.account
        if request.method == 'POST':
            try:
                schema = AccountSettings()
                values = request.params
                data = schema.deserialize(values)
                if not data['password1'] == data['password2']:
                    raise colander.Invalid(AccountSettings.password1,
                                           _("Passwords don't match!"))

                c.account.fullname = data['fullname']
                c.account.script_root = data['script_root']
                c.account.email = data['email']
                if data['password1'] is not None and len(data['password1']):
                    c.account.password = generate_password_hash(data['password1'])
                db.session.add(c.account)
                db.session.commit()
                h.flash_success(_("Your settings have been updated."))
            except colander.Invalid, i:
                errors = i.asdict()
        else:
            values = c.account.as_dict()
        return render('account/settings.html',
                      form_fill=values,
                      form_errors=errors)

    def complete(self, format='json'):
        parser = DistinctParamParser(request.params)
        params, errors = parser.parse()
        if errors:
            response.status = 400
            return {'errors': errors}

        query = db.session.query(Account)
        filter_string = params.get('q') + '%'
        query = query.filter(db.or_(Account.name.ilike(filter_string),
                                    Account.fullname.ilike(filter_string)))
        count = query.count()
        query = query.limit(params.get('pagesize'))
        query = query.offset(int((params.get('page') - 1) * params.get('pagesize')))
        return to_jsonp({
            'results': list(query),
            'count': count
            })

    def after_login(self):
        if c.account is not None:
            h.flash_success(_("Welcome back, %s!") % c.account.name)
            redirect("/")
        else:
            h.flash_error(_("Incorrect user name or password!"))
            redirect("/login")

    def after_logout(self):
        h.flash_success(_("You have been logged out."))
        redirect("/")
