from pylons import config

import logging

import colander

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.i18n import _

from repoze.who.api import get_api

from openspending.model import meta as db, Dataset
from openspending.model.account import Account, AccountRegister, \
    AccountSettings
from openspending.lib.paramparser import DistinctParamParser
from openspending.ui.lib import helpers as h
from openspending.ui.lib.base import BaseController, require
from openspending.ui.lib.security import generate_password_hash
from openspending.ui.lib.mailman import subscribe_lists
from openspending.lib.jsonexport import to_jsonp
from openspending.lib.mailer import send_reset_link
from openspending.ui.alttemplates import templating
from sqlalchemy.sql.expression import desc
log = logging.getLogger(__name__)


class AccountController(BaseController):

    def login(self):
        """
        Render the login page (which is also the registration page)
        """

        # Disable cache
        self._disable_cache()

        # Add config (so we can offer users to subscribe to mailing lists)
        c.config = config

        # Return the rendered template
        return templating.render('account/login.html')

    def register(self):
        """
        Perform registration of a new user
        """

        # We must allow account creation
        require.account.create()

        # We add the config as a context variable in case anything happens
        # (like with login we need this to allow subscriptions to mailing lists)
        c.config = config

        # Disable the cache (don't want anything getting in the way)
        self._disable_cache()

        # Initial values and errors
        errors, values = {}, None

        # If this is a POST operation somebody is trying to register
        if request.method == 'POST':
            try:
                # Get the account register schema (for validation)
                schema = AccountRegister()

                # Set values from the request parameters
                # (for validation and so we can autofill forms)
                values = request.params

                # Grab the actual data and validate it
                data = schema.deserialize(values)

                # Check if the username already exists, return an error if so
                if Account.by_name(data['name']):
                    raise colander.Invalid(
                        AccountRegister.name,
                        _("Login name already exists, please choose a "
                          "different one"))

                # Check if passwords match, return error if not
                if not data['password1'] == data['password2']:
                    raise colander.Invalid(AccountRegister.password1,
                                           _("Passwords don't match!"))

                # Create the account
                account = Account()

                # Set username and full name
                account.name = data['name']
                account.fullname = data['fullname']

                # Set email and if email address should be public
                account.email = data['email']
                account.public_email = data['public_email']

                # Hash the password and store the hash
                account.password = generate_password_hash(data['password1'])

                # Commit the new user account to the database
                db.session.add(account)
                db.session.commit()

                # Perform a login for the user
                who_api = get_api(request.environ)
                authenticated, headers = who_api.login({
                    "login": account.name,
                    "password": data['password1']
                })
                # Add the login headers
                response.headers.extend(headers)

                # Subscribe the user to the mailing lists
                errors = subscribe_lists(('community', 'developer'), data)
                # Notify if the mailing list subscriptions failed
                if errors:
                    h.flash_notice(_("Subscription to the following mailing " +
                                     "lists probably failed: %s.") % ', '.join(errors))

                # Registration successful - Redirect to the front page
                return redirect("/")
            except colander.Invalid, i:
                # Mark colander errors
                errors = i.asdict()

        # Show the templates (with possible errors and form values)
        return templating.render('account/login.html', form_fill=values,
                                 form_errors=errors)

    def settings(self):
        """
        Change settings for the logged in user
        """

        # The logged in user must be able to update the account
        require.account.update(c.account)

        # Disable the cache
        self._disable_cache()

        # Initial values and errors
        errors, values = {}, c.account

        # If POST the user is trying to update the settings
        if request.method == 'POST':
            try:
                # Get the account settings schema (for validation)
                schema = AccountSettings()

                # Set values from the request parameters
                # (for validation and so we can autofill forms)
                values = request.params

                # Grab the actual data and validate it
                data = schema.deserialize(values)

                # If the passwords don't match we notify the user
                if not data['password1'] == data['password2']:
                    raise colander.Invalid(AccountSettings.password1,
                                           _("Passwords don't match!"))

                # Update full name
                c.account.fullname = data['fullname']

                # Update the script root
                c.account.script_root = data['script_root']

                # Update email and whether email should be public
                c.account.email = data['email']
                c.account.public_email = data['public_email']

                # If twitter handle is provided we update it
                # (and if it should be public)
                if data['twitter'] is not None:
                    c.account.twitter_handle = data['twitter'].lstrip('@')
                    c.account.public_twitter = data['public_twitter']

                # If a new password was provided we update it as well
                if data['password1'] is not None and len(data['password1']):
                    c.account.password = generate_password_hash(data['password1'])

                # Do the actual update in the database
                db.session.add(c.account)
                db.session.commit()

                # Let the user know we've updated successfully
                h.flash_success(_("Your settings have been updated."))
            except colander.Invalid, i:
                # Load errors if we get here
                errors = i.asdict()
        else:
            # Get the account values to autofill the form
            values = c.account.as_dict()

            # We need to put public checks separately because they're not 
            # a part of the dictionary representation of the account
            if c.account.public_email:
                values['public_email'] = c.account.public_email
            if c.account.public_twitter:
                values['public_twitter'] = c.account.public_twitter

        # Return the rendered template
        return templating.render('account/settings.html',
                                 form_fill=values,
                                 form_errors=errors)

    def dashboard(self, format='html'):
        """
        Show the user profile for the logged in user
        """

        # To be able to show it, the user must be logged in
        require.account.logged_in()

        # Disable caching
        self._disable_cache()

        # Return the profile page for the user
        return self.profile(c.account.name)

    def scoreboard(self, format='html'):
        """
        A list of users ordered by their score. The score is computed by
        by assigning every dataset a score (10 divided by number of maintainers)
        and then adding that score up for all maintainers.

        This does give users who maintain a single dataset a higher score than
        those who are a part of a maintenance team, which is not really what 
        we want (since that rewards single points of failure in the system).

        But this is an adequate initial score and this will only be accessible
        to administrators (who may be interested in findin these single points
        of failures).
        """

        # If user is not an administrator we abort
        if not (c.account and c.account.admin):
            abort(403, _("You are not authorized to view this page"))

        # Assign scores to each dataset based on number of maintainers
        score = db.session.query(Dataset.id,
                                 (10/db.func.count(Account.id)).label('sum'))
        score = score.join('managers').group_by(Dataset.id).subquery()

        # Order users based on their score which is the sum of the dataset
        # scores they maintain
        user_score = db.session.query(Account.name, Account.email,
                                      db.func.coalesce(db.func.sum(score.c.sum),0).label('score'))
        user_score = user_score.outerjoin(Account.datasets).outerjoin(score)
        user_score = user_score.group_by(Account.name, Account.email)
        # We exclude the system user
        user_score = user_score.filter(Account.name != 'system')
        user_score = user_score.order_by(desc('score'))

        # Fetch all and assign to a context variable score and paginate them
        # We paginate 42 users per page, just because that's an awesome number
        scores = user_score.all()
        c.page = templating.Page(scores, items_per_page=42,
                                 item_count=len(scores),
                                 **request.params)

        return templating.render('account/scoreboard.html')

    def complete(self, format='json'):
        self._disable_cache()
        parser = DistinctParamParser(request.params)
        params, errors = parser.parse()
        if errors:
            response.status = 400
            return {'errors': errors}
        if not c.account:
            response.status = 403
            return to_jsonp({'errors': _("You are not authorized to see that "
                                         "page")})

        query = db.session.query(Account)
        filter_string = params.get('q') + '%'
        query = query.filter(db.or_(Account.name.ilike(filter_string),
                                    Account.fullname.ilike(filter_string)))
        count = query.count()
        query = query.limit(params.get('pagesize'))
        query = query.offset(int((params.get('page') - 1) *
                                 params.get('pagesize')))
        results = [dict(fullname=x.fullname, name=x.name) for x in list(query)]

        return to_jsonp({
            'results': results,
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
        """
        Allow user to trigger a reset of the password in case they forget it
        """

        # Disable the cache
        self._disable_cache()

        # If it's a simple GET method we return the form
        if request.method == 'GET':
            return templating.render('account/trigger_reset.html')

        # Get the email
        email = request.params.get('email')

        # Simple check to see if the email was provided. Flash error if not
        if email is None or not len(email):
            h.flash_error(_("Please enter an email address!"))
            return templating.render('account/trigger_reset.html')

        # Get the account for this email
        account = Account.by_email(email)

        # If no account is found we let the user know that it's not registered
        if account is None:
            h.flash_error(_("No user is registered under this address!"))
            return templating.render('account/trigger_reset.html')

        # Send the reset link to the email of this account
        send_reset_link(account)

        # Let the user know that email with link has been sent
        h.flash_success(_("You've received an email with a link to reset your "
                          + "password. Please check your inbox."))

        # Redirect to the login page
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
        """
        Generate a profile page for a user (from the provided name)
        """

        # Get the account, if it's none we return a 404
        account = Account.by_name(name)
        if account is None:
            response.status = 404
            return None

        # Set the account we got as the context variable 'profile'
        # Note this is not the same as the context variable 'account'
        # which is the account for a logged in user
        c.profile = account

        # Set a context boo if email/twitter should be shown, it is only shown
        # to administrators and to owner (account is same as context account)
        show_info = (c.account and c.account.admin) or (c.account == account)

        # ..or if the user has chosen to make it public 
        c.show_email = show_info or account.public_email
        c.show_twitter = show_info or account.public_twitter

        # Collect and sort the account's datasets and views
        c.account_datasets = sorted(account.datasets, key=lambda d: d.label)
        c.account_views = sorted(account.views, key=lambda d: d.label)

        # Render the profile
        return templating.render('account/profile.html')
