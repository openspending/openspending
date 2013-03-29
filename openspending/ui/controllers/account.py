from pylons import config

import logging

import colander

from pylons import app_globals, request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from repoze.who.api import get_api

from openspending.model import meta as db, Dataset
from openspending.model.account import Account, AccountRegister, \
    AccountSettings
from openspending.lib.paramparser import DistinctParamParser
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, render, require
from openspending.ui.lib.security import generate_password_hash
from openspending.ui.lib.mailman import subscribe_lists
from openspending.lib.jsonexport import to_jsonp
from openspending.lib.mailer import send_reset_link

log = logging.getLogger(__name__)


class AccountController(BaseController):

    def login(self):
        self._disable_cache()
        c.config = config
        return render('account/login.html')

    def register(self):
        require.account.create()
        self._disable_cache()
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

                errors = subscribe_lists(('community', 'developer'), data)
                if errors:
                    h.flash_notice(_("Subscription to the following mailing " +
                            "lists probably failed: %s.") % ', '.join(errors))

                response.headers.extend(headers)
                return redirect("/")
            except colander.Invalid, i:
                errors = i.asdict()
        return render('account/login.html', form_fill=values,
                form_errors=errors)

    def settings(self):
        require.account.update(c.account)
        self._disable_cache()
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

    def dashboard(self, format='html'):
        require.account.logged_in()
        self._disable_cache()
        c.account_datasets = sorted(c.account.datasets, key=lambda d: d.label)
        c.account_views = sorted(c.account.views, key=lambda d: d.label)
        return render('account/dashboard.html')

    def complete(self, format='json'):
        self._disable_cache()
        if not (c.account and c.account.admin):
            response.status = 403
            return to_jsonp({'errors': _("You are not authorized to see that page")})
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
        self._disable_cache()
        if c.account is not None:
            h.flash_success(_("Welcome back, %s!") % c.account.name)
            redirect(h.url_for(controller='account', action='dashboard'))
        else:
            h.flash_error(_("Incorrect user name or password!"))
            redirect(h.url_for(controller='account', action='login'))

    def after_logout(self):
        self._disable_cache()
        h.flash_success(_("You have been logged out."))
        redirect("/")

    def trigger_reset(self):
        self._disable_cache()
        if request.method == 'GET':
            return render('account/trigger_reset.html')
        email = request.params.get('email')
        if email is None or not len(email):
            h.flash_error(_("Please enter an email address!"))
            return render('account/trigger_reset.html')
        account = Account.by_email(email)
        if account is None:
            h.flash_error(_("No user is registered under this address!"))
            return render('account/trigger_reset.html')
        send_reset_link(account)

        h.flash_success(_("You've received an email with a link to reset your "
            + "password. Please check your inbox."))
        redirect(h.url_for(controller='account', action='login'))

    def do_reset(self):
        email = request.params.get('email')
        if email is None or not len(email):
            h.flash_error(_("The reset link is invalid!"))
            redirect(h.url_for(controller='account', action='login'))
        account = Account.by_email(email)
        if account is None:
            h.flash_error(_("No user is registered under this address!"))
            redirect(h.url_for(controller='account', action='login'))
        if request.params.get('token') != account.token:
            h.flash_error(_("The reset link is invalid!"))
            redirect(h.url_for(controller='account', action='login'))
        who_api = request.environ['repoze.who.plugins']['auth_tkt']
        headers = who_api.remember(request.environ,
                {'repoze.who.userid': account.name})
        response.headers.extend(headers)
        h.flash_success(_("Thanks! You have now been signed in - please change "
            + "your password!"))
        redirect(h.url_for(controller='account', action='settings'))

    def profile(self, name=None):
        c.config = config
        account = Account.by_name(name)
        if account is None:
            response.status = 404
            return None
        c.profile = account
        c.is_admin = True if (c.account and c.account.admin is True) else False
        return render('account/profile.html')
