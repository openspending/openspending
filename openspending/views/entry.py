from flask import Blueprint, render_template

blueprint = Blueprint('entry', __name__)


@blueprint.route('/<dataset>/entries')
def index(dataset):
    return render_template('home/index.html')


@blueprint.route('/search')
def search():
    return render_template('home/index.html')

