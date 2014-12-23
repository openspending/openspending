from flask import Blueprint, render_template

blueprint = Blueprint('dimension', __name__)


@blueprint.route('/<dataset>/dimensions')
def index(dataset):
    return render_template('home/index.html')


@blueprint.route('/<dataset>/dimensions/<dimension>')
def view(dataset, dimension):
    return render_template('home/index.html')


@blueprint.route('/<dataset>/dimensions/<dimension>/<name>')
def member(dataset, dimension, name):
    return render_template('home/index.html')

