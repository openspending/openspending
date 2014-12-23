from flask import Blueprint, render_template

blueprint = Blueprint('api', __name__)


@blueprint.route('/api/2/search')
def search():
    return render_template('home/index.html')
