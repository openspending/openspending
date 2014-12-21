from flask import Blueprint, render_template

blueprint = Blueprint('account', __name__)


@blueprint.route('/dashboard')
def dashboard():
    return render_template('home/index.html')


@blueprint.route('/settings')
def settings():
    return render_template('home/index.html')

