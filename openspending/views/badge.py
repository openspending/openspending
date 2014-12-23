import logging

from flask import Blueprint, render_template, redirect, request
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import BadRequest

from openspending.core import db, badge_images
from openspending.model.badge import Badge
from openspending.auth import require
from openspending.lib.jsonexport import jsonify
from openspending.lib.helpers import url_for, obj_or_404, get_dataset
from openspending.lib.hypermedia import badge_apply_links


log = logging.getLogger(__name__)
blueprint = Blueprint('badge', __name__)


@blueprint.route('/badges/index.<format>')
@blueprint.route('/badges')
def index(format='html'):
    """
    List all badges in the system. Default is to present the
    user with an html site, but the user can request a json list
    of badges.
    """
    badges = Badge.all()

    # If the requested format is json return a list of badges
    if format == 'json':
        badges = [badge_apply_links(b.as_dict()) for b in badges]
        return jsonify({"badges": badges})

    return render_template('badge/index.html', badges=badges)


@blueprint.route('/badge/<id>')
@blueprint.route('/badge/<id>.<format>')
def information(id, format='html'):
    """
    Show information about the badge. Default is to present the
    user with the badge on an html site, but the user can request a
    json representation of the badge
    """
    badge = obj_or_404(Badge.by_id(id=id))

    # Return a json representation if the format requested is 'json'
    if format == 'json':
        return jsonify({"badge": badge_apply_links(badge.as_dict())})

    return render_template('badge/information.html', badge=badge)


@blueprint.route('/badges/create', methods=['POST'])
def create():
    """ Create a new badge in the system """
    require.badge.create()

    # TODO: some data validation wouldn't hurt.

    values = dict(request.form.items())
    upload_image_path = badge_images.save(request.files['image'])
    badge = Badge(values.get('label'),
                  upload_image_path,
                  values.get('description'),
                  current_user)
    db.session.add(badge)
    db.session.commit()

    return redirect(url_for('badge.information', id=badge.id))


@blueprint.route('/<dataset>/give', methods=['POST'])
def give(dataset):
    """
    Award a given badge to a given dataset.
    """
    dataset = get_dataset(dataset)

    # Get the badge
    badge = Badge.by_id(id=request.form.get('badge'))

    if badge:
        # See if user can award this badge to a this dataset
        require.badge.give(badge, dataset)
        # Add the dataset to the badge datasets and commit to database
        badge.datasets.append(dataset)
        db.session.commit()
    else:
        raise BadRequest(_('Badge not found.'))

    # Go to the dataset's main page
    return redirect(url_for('dataset.about', dataset=dataset.name))
