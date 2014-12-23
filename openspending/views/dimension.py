from flask import Blueprint, render_template

blueprint = Blueprint('dimension', __name__)


@blueprint.route('/<dataset>/dimensions')
def index(dataset):
    return render_template('home/index.html')


