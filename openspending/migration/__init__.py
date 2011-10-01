import imp
import logging
import os
import re

from openspending import mongo

log = logging.getLogger(__name__)

FILENAME_RE = re.compile(r'^\d{8}T\d{6}\-[a-zA-Z0-9\-]+\.py$')

class MigrationError(Exception):
    pass

class IrreversibleMigrationError(MigrationError):
    pass

class NullVersion(object):
    def __cmp__(self, other):
        return -1

    def __str__(self):
        return "<NullVersion>"

root = None

def configure(dirname):
    global root
    root = dirname

def up():
    _check_migrations_dir()

    log.info("Starting migrations at version '%s'", current_version())

    for m in pending_migrations():
        run_migration(m)

    log.info("Ending migrations at version '%s'", current_version())

def current_version():
    obj = mongo.db.migrate.find_one()
    if obj:
        return obj['version']
    else:
        return NullVersion()

def set_version(version):
    obj = mongo.db.migrate.find_one()
    if obj:
        mongo.db.migrate.update(obj, {'$set': {'version': version}})
    else:
        mongo.db.migrate.insert({'version': version})

def pending_migrations():
    m = all_migrations()
    while m and m[0] <= current_version():
        m.pop(0)
    return m

def all_migrations():
    files = os.listdir(root)
    files = filter(lambda f: FILENAME_RE.match(f), files)
    migrations = map(lambda f: f[0:-3], files)
    return sorted(migrations)

def run_migration(migration, force=False):
    if migration <= current_version():
        if force:
            log.warn("Forcing dodgy migration!")
        else:
            raise MigrationError("Attempting to migrate to version '%s', "
                                 "which is less than or the same as the "
                                 "current version, '%s', without 'force=True'",
                                 migration, current_version())

    log.info("Running migration: %s -> %s", current_version(), migration)

    mig_file = os.path.join(root, "%s.py" % migration)
    mig_mod = imp.load_module(os.path.basename(mig_file)[0:-3],
                              open(mig_file),
                              mig_file,
                              ('.py', 'r', imp.PY_SOURCE))

    mig_mod.up()
    set_version(migration)

def _check_migrations_dir():
    if not root:
        raise MigrationError("Migration root not set! "
                             "Have you called migration.configure()?")

    try:
        open(os.path.join(root, '.migration'))
    except IOError as e:
        raise MigrationError("Migration root '%s' doesn't look like "
                             "a migration directory (.migration doesn't "
                             "exist). Aborting!")
