from flask import Blueprint, render_template

blueprint = Blueprint('dataset', __name__)


@blueprint.route('/datasets')
def index():
    return render_template('home/index.html')


@blueprint.route('/datasets/new')
def new():
    return render_template('home/index.html')


@blueprint.route('/datasets.rss')
def feed_rss():
    return render_template('home/index.html')
