from flask import Blueprint, render_template

blueprint = Blueprint('view', __name__)


@blueprint.route('/<dataset>/views/new')
def new(dataset):
    return render_template('home/index.html')
