import colander
from flask import Blueprint, render_template, request, redirect
from flask.ext.login import current_user, login_user, logout_user
from flask.ext.babel import gettext
from sqlalchemy.sql.expression import desc, func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from openspending.core import db, login_manager
from openspending.auth import require
from openspending.model.dataset import Dataset
from openspending.model.account import (Account, AccountRegister,
                                        AccountSettings)
from openspending.lib.paramparser import DistinctParamParser
from openspending.lib.mailman import subscribe_lists
#from openspending.lib.jsonexport import to_jsonp
#from openspending.lib.mailer import send_reset_link
from openspending.views.helpers import url_for, obj_or_404
from openspending.views.helpers import disable_cache, flash_error
from openspending.views.helpers import flash_notice, flash_success
from openspending.lib.pagination import Page


blueprint = Blueprint('account', __name__)


@disable_cache
@blueprint.route('/login', methods=['GET'])
def login():
    """
    Render the login page (which is also the registration page)
    """
    return render_template('account/login.html')


@blueprint.route('/login', methods=['POST', 'PUT'])
def login_perform():
    account = Account.by_name(request.form.get('login'))
    if account is not None:
        if check_password_hash(account.password, request.form.get('password')):
            login_user(account, remember=True)
            flash_success(gettext("Welcome back, %(name)s!", name=account.name))
            return redirect(url_for('account.dashboard'))
    flash_error(gettext("Incorrect user name or password!"))
    return login()


@disable_cache
@blueprint.route('/register')
def register():
    """
    Perform registration of a new user
    """

    # We must allow account creation
    require.account.create()

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
                    gettext("Login name already exists, please choose a "
                            "different one"))

            # Check if passwords match, return error if not
            if not data['password1'] == data['password2']:
                raise colander.Invalid(AccountRegister.password1,
                                       gettext("Passwords don't match!"))

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
            login_user(account, remember=True)

            # Subscribe the user to the mailing lists
            errors = subscribe_lists(('community', 'developer'), data)
            # Notify if the mailing list subscriptions failed
            if errors:
                flash_notice(gettext("Subscription to the following mailing " +
                                     "lists probably failed: %s.") % ', '.join(errors))

            # Registration successful - Redirect to the front page
            return redirect(url_for('home.index'))
        except colander.Invalid as i:
            # Mark colander errors
            errors = i.asdict()

    # Show the templates (with possible errors and form values)
    return render_template('account/login.html', form_fill=values,
                           form_errors=errors)


@disable_cache
@blueprint.route('/settings')
def settings():
    """
    Change settings for the logged in user
    """
    # The logged in user must be able to update the account
    require.account.update(current_user)

    # Initial values and errors
    errors, values = {}, current_user

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
                                       gettext("Passwords don't match!"))

            # Update full name
            current_user.fullname = data['fullname']

            # Update the script root
            current_user.script_root = data['script_root']

            # Update email and whether email should be public
            current_user.email = data['email']
            current_user.public_email = data['public_email']

            # If twitter handle is provided we update it
            # (and if it should be public)
            if data['twitter'] is not None:
                current_user.twitter_handle = data['twitter'].lstrip('@')
                current_user.public_twitter = data['public_twitter']

            # If a new password was provided we update it as well
            if data['password1'] is not None and len(data['password1']):
                current_user.password = generate_password_hash(
                    data['password1'])

            # Do the actual update in the database
            db.session.add(current_user)
            db.session.commit()

            # Let the user know we've updated successfully
            flash_success(gettext("Your settings have been updated."))
        except colander.Invalid as i:
            # Load errors if we get here
            errors = i.asdict()
    else:
        # Get the account values to autofill the form
        values = current_user.as_dict()

        # We need to put public checks separately because they're not
        # a part of the dictionary representation of the account
        if current_user.public_email:
            values['public_email'] = current_user.public_email
        if current_user.public_twitter:
            values['public_twitter'] = current_user.public_twitter

    # Return the rendered template
    return render_template('account/settings.html',
                           form_fill=values,
                           form_errors=errors)


@disable_cache
@blueprint.route('/dashboard')
def dashboard(format='html'):
    """
    Show the user profile for the logged in user
    """
    require.account.logged_in()
    return profile(current_user.name)


@blueprint.route('/scoreboard')
def scoreboard(format='html'):
    """
    A list of users ordered by their score. The score is computed by
    by assigning every dataset a score (10 divided by no. of maintainers)
    and then adding that score up for all maintainers.

    This does give users who maintain a single dataset a higher score than
    those who are a part of a maintenance team, which is not really what
    we want (since that rewards single points of failure in the system).

    But this is an adequate initial score and this will only be accessible
    to administrators (who may be interested in findin these single points
    of failures).
    """

    # If user is not an administrator we abort
    if not (current_user and current_user.admin):
        abort(403, gettext("You are not authorized to view this page"))

    # Assign scores to each dataset based on number of maintainers
    score = db.session.query(Dataset.id,
                             (10 / func.count(Account.id)).label('sum'))
    score = score.join('managers').group_by(Dataset.id).subquery()

    # Order users based on their score which is the sum of the dataset
    # scores they maintain
    user_score = db.session.query(
        Account.name, Account.email,
        func.coalesce(func.sum(score.c.sum), 0).label('score'))
    user_score = user_score.outerjoin(Account.datasets).outerjoin(score)
    user_score = user_score.group_by(Account.name, Account.email)
    # We exclude the system user
    user_score = user_score.filter(Account.name != 'system')
    user_score = user_score.order_by(desc('score'))

    # Fetch all and assign to a context variable score and paginate them
    # We paginate 42 users per page, just because that's an awesome number
    scores = user_score.all()
    c.page = Page(scores, items_per_page=42,
                  item_count=len(scores),
                  **request.params)

    return render_template('account/scoreboard.html')


@disable_cache
@blueprint.route('/accounts/_complete')
def complete(format='json'):
    parser = DistinctParamParser(request.params)
    params, errors = parser.parse()
    if errors:
        response.status = 400
        return {'errors': errors}
    if current_user.is_authenticated():
        response.status = 403
        return to_jsonp({'errors': gettext("You are not authorized to see that "
                                     "page")})

    query = db.session.query(Account)
    filter_string = params.get('q') + '%'
    query = query.filter(or_(Account.name.ilike(filter_string),
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


@disable_cache
@blueprint.route('/logout')
def logout():
    logout_user()
    flash_success(gettext("You have been logged out."))
    return redirect(url_for('home.index'))


@disable_cache
@blueprint.route('/account/forgotten')
def trigger_reset():
    """
    Allow user to trigger a reset of the password in case they forget it
    """
    # If it's a simple GET method we return the form
    if request.method == 'GET':
        return render_template('account/trigger_reset.html')

    # Get the email
    email = request.params.get('email')

    # Simple check to see if the email was provided. Flash error if not
    if email is None or not len(email):
        flash_error(gettext("Please enter an email address!"))
        return render_template('account/trigger_reset.html')

    # Get the account for this email
    account = Account.by_email(email)

    # If no account is found we let the user know that it's not registered
    if account is None:
        flash_error(gettext("No user is registered under this address!"))
        return render_template('account/trigger_reset.html')

    # Send the reset link to the email of this account
    send_reset_link(account)

    # Let the user know that email with link has been sent
    flash_success(gettext("You've received an email with a link to reset your "
                          "password. Please check your inbox."))

    # Redirect to the login page
    return redirect(url_for('account.login'))


@blueprint.route('/account/reset')
def do_reset(self):
    email = request.args.get('email')
    if email is None or not len(email):
        flash_error(gettext("The reset link is invalid!"))
        return redirect(url_for('account.login'))

    account = Account.by_email(email)
    if account is None:
        flash_error(gettext("No user is registered under this address!"))
        return redirect(url_for('account.login'))

    if request.args.get('token') != account.token:
        flash_error(gettext("The reset link is invalid!"))
        return redirect(url_for('account.login'))

    login_user(account)
    flash_success(
        gettext("Thanks! You have now been signed in - please change "
                + "your password!"))
    return redirect(url_for('account.settings'))


@blueprint.route('/account/<name>')
def profile(name):
    """ Generate a profile page for a user (from the provided name) """

    # Get the account, if it's none we return a 404
    profile = obj_or_404(Account.by_name(name))

    # Set a context boo if email/twitter should be shown, it is only shown
    # to administrators and to owner (account is same as context account)
    show_info = (current_user and current_user.admin) or \
                (current_user.id == profile.id)

    # ..or if the user has chosen to make it public
    show_email = show_info or profile.public_email
    show_twitter = show_info or profile.public_twitter

    # Collect and sort the account's datasets and views
    profile_datasets = sorted(profile.datasets, key=lambda d: d.label)
    profile_views = sorted(profile.views, key=lambda d: d.label)

    # Render the profile
    return render_template('account/profile.html', profile=profile,
                           show_email=show_email, show_twitter=show_twitter,
                           profile_datasets=profile_datasets,
                           profile_views=profile_views)
