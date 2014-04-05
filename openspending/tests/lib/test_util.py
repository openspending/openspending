# coding=utf8

from openspending.lib import util

from openspending.tests import helpers as h


def test_slugify():
    h.assert_equal(util.slugify(u'foo'), 'foo')
    h.assert_equal(util.slugify(u'fóo'), 'foo')
    h.assert_equal(util.slugify(u'fóo&bañ'), 'foo-ban')


def test_hash_values():
    util.hash_values([u'fóo&bañ'])


def test_sort_by_reference():
    ids = [4, 7, 1, 3]
    objs = [{'id': 1}, {'id': 7}, {'id': 4}, {'id': 3}]

    sorted_ = util.sort_by_reference(ids, objs, lambda x: x['id'])

    h.assert_equal(sorted_, [{'id': 4}, {'id': 7}, {'id': 1}, {'id': 3}])
