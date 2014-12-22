from flask import Blueprint, render_template

blueprint = Blueprint('editor', __name__)


@blueprint.route('/<dataset>/editor')
def index(dataset):
    return render_template('home/index.html')
