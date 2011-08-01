"""
Copyright (c) 2011, Daniel Crosta <dcrosta@late.am>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

__all__ = ('dump', 'restore')

import cPickle
import sys
from pymongo.database import Database


def dump(database, filename, collections=None):
    # dump the entire contents of the database to the
    # file named by `filename`. This method makes no
    # attempt to ensure that the data size will fit in
    # a single file on the user's filesystem or in
    # memory, so users should not attempt to dump
    # especially large databases without modifying this
    # function to work more efficiently.

    record = {
        'collections': {},
        'indexes': {},
        'javascripts': {}
    }

    for name in database.collection_names():
        if name.startswith('system.'):
            continue
        if collections is not None and name not in collections:
            continue

        collection = database[name]
        record['collections'][name] = list(collection.find())
        record['indexes'][name] = collection.index_information()

    for name in database.system_js.list():
        code = database.system.js.find_one({'_id': name})['value']
        record['javascripts'][name] = code

    cPickle.dump(record, file(filename, 'w+b'))

def restore(database, filename, drop=True):
    # restore a previously pymongodumped file to the
    # given database, optionally first dropping the
    # database to ensure a clean restore of the file's
    # contents

    record = cPickle.load(file(filename, 'r+b'))

    for name in record['collections']:
        if drop and name in database.collection_names():
            database.drop_collection(name)

        collection = database[name]
        documents = record['collections'][name]
        for batch in _chunk_iterator(documents):
            if batch:
                collection.insert(batch, safe=True)

        for index in record['indexes'][name].itervalues():
            if index['key'] == [('_id', 1)]:
                # don't re-create the default index
                continue

            kwargs = {}
            kwargs['sparse'] = 'sparse' in index and index['sparse']
            kwargs['dropDups'] = 'dropDups' in index and index['dropDups']
            kwargs['background'] = False

            collection.ensure_index(index['key'], **kwargs)

    for name, code in record['javascripts'].iteritems():
        setattr(database.system_js, name, code)


def _chunk_iterator(iterable, chunk_size=100):
    out = []
    for thing in iterable:
        if len(out) < chunk_size:
            out.append(thing)
        else:
            yield out
            out = [thing]
    yield out

if __name__ == '__main__':
    from optparse import OptionParser
    import pymongo
    parser = OptionParser('%prog [options] action database filename')
    parser.description = 'action is either "dump" or "restore"'
    parser.set_defaults(
        hostname='localhost',
        port=27017,
    )
    parser.remove_option('-h') # we're going to override it
    parser.add_option('-h', '--host', action='store', dest='hostname', help='Host name to connect to')
    parser.add_option('-p', '--port', action='store', dest='port', help='Port number to connect to')
    parser.add_option('-d', '--database', action='store', dest='database', help='Database to operate on')
    parser.add_option('-?', '--help', action='help', help='Show this help message')

    options, args = parser.parse_args()

    if len(args) != 3:
        sys.exit(parser.error('action, database, and filename required'))

    action, dbname, filename = args
    action = action.lower()
    if action not in ('dump', 'restore'):
        sys.exit(parser.error('action must be "dump" or "restore"'))

    conn = pymongo.Connection(
        host=options.hostname,
        port=int(options.port),
    )
    database = conn[dbname]

    if action == 'restore':
        restore(database, filename)
    else:
        dump(database, filename)

