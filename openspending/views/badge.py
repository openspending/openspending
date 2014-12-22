from flask import Blueprint, render_template

blueprint = Blueprint('badge', __name__)


@blueprint.route('/xxxx')
def information():
    return render_template('home/index.html')

