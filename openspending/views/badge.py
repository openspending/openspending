from flask import Blueprint, render_template

blueprint = Blueprint('badge', __name__)


@blueprint.route('/badges')
@blueprint.route('/badges.<format>')
def index(format='html'):
    return render_template('home/index.html')


@blueprint.route('/badges/create')
def create(format='html'):
    return render_template('home/index.html')


@blueprint.route('/badge/<id>')
def information(id):
    return render_template('home/index.html')


@blueprint.route('/<dataset>/give', methods=['POST'])
def give(dataset):
    return render_template('home/index.html')
