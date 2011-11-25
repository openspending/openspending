# coding=utf8

from openspending.lib import util

from ... import helpers as h

def test_slugify():
    h.assert_equal(util.slugify(u'foo'), 'foo')
    h.assert_equal(util.slugify(u'fóo'), 'foo')
    h.assert_equal(util.slugify(u'fóo&bañ'), 'foo-ban')

def test_hash_values():
    util.hash_values([u'fóo&bañ'])
