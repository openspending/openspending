import os
import tempfile
import shutil

from openspending import migration, mongo
from openspending.test import DatabaseTestCase, helpers as h

class TestMigration(DatabaseTestCase):
    def setup(self):
        super(TestMigration, self).setup()
        migration.root = None
        self.dir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.dir)
        super(TestMigration, self).teardown()

    def setup_migrations(self):
        migration.configure(dirname=self.dir)
        files_to_create = ('.migration',
                           '20100901T100000-first-one.py',
                           '20100901T103000-number-2.py',
                           '20101002T113000-tertiary.py',
                           '20101002T113000-tertiary.pyc',
                           '20100901T100001-CAPITALS.py',
                           'distraction.txt')

        for name in files_to_create:
            open(os.path.join(self.dir, name), 'w').close()

        f = open(os.path.join(self.dir, files_to_create[1]), 'w')
        f.write("""
from openspending import mongo

def up():
    mongo.db.foobar.insert({'foo': 'bar'})
        """)
        f.close()

        f = open(os.path.join(self.dir, files_to_create[2]), 'w')
        f.write("""
from openspending import mongo

def up():
    mongo.db.foobar.update({'foo': 'bar'}, {'$set': {'foo': 'baz'}})
        """)
        f.close()

    def test_unconfigured(self):
        h.assert_raises_regexp(migration.MigrationError,
                               "root not set",
                               migration.up)

    def test_null_version(self):
        v = migration.current_version()
        h.assert_true(isinstance(v, migration.NullVersion),
                      "Migration current version wasn't the null version!")

    def test_set_version(self):
        migration.set_version('foobar')
        h.assert_equal(migration.current_version(), 'foobar')
        migration.set_version('bazbar')
        h.assert_equal(migration.current_version(), 'bazbar')

    def test_configure(self):
        migration.configure(dirname=self.dir)
        h.assert_equal(migration.root, self.dir)

    def test_dotmigration_check(self):
        migration.configure(dirname=self.dir)
        h.assert_raises_regexp(migration.MigrationError,
                               ".migration doesn't exist",
                               migration.up)

    def test_all_migrations(self):
        self.setup_migrations()
        h.assert_equal(migration.all_migrations(),
                       ['20100901T100000-first-one',
                        '20100901T100001-CAPITALS',
                        '20100901T103000-number-2',
                        '20101002T113000-tertiary'])

    @h.patch('openspending.migration.current_version')
    def test_pending_migrations(self, vers_mock):
        self.setup_migrations()
        vers_mock.return_value = '20100901T100000-first-one'
        h.assert_equal(migration.pending_migrations(),
                       ['20100901T100001-CAPITALS',
                        '20100901T103000-number-2',
                        '20101002T113000-tertiary'])

        vers_mock.return_value = '20100901T100001-CAPITALS'
        h.assert_equal(migration.pending_migrations(),
                       ['20100901T103000-number-2',
                        '20101002T113000-tertiary'])

        vers_mock.return_value = '20100901T103000-number-2'
        h.assert_equal(migration.pending_migrations(),
                       ['20101002T113000-tertiary'])

        vers_mock.return_value = '20101002T113000-tertiary'
        h.assert_equal(migration.pending_migrations(), [])

        vers_mock.return_value = '20200101T000000-farfuture'
        h.assert_equal(migration.pending_migrations(), [])

        vers_mock.return_value = '19700101T000000-distantpast'
        h.assert_equal(migration.pending_migrations(),
                       ['20100901T100000-first-one',
                        '20100901T100001-CAPITALS',
                        '20100901T103000-number-2',
                        '20101002T113000-tertiary'])

    @h.patch('openspending.migration.current_version')
    def test_run_migration_wrongway(self, vers_mock):
        self.setup_migrations()
        vers_mock.return_value = '20100901T100001-CAPITALS'

        # Should raise with force=False
        h.assert_raises_regexp(migration.MigrationError,
                               "less than or the same as",
                               migration.run_migration,
                               '20100901T100000-first-one')

        # Should not raise
        migration.run_migration('20100901T100000-first-one', force=True)

    def test_run_migration(self):
        self.setup_migrations()
        migration.run_migration('20100901T100000-first-one')

        h.assert_equal(migration.current_version(),
                       '20100901T100000-first-one')

        h.assert_equal(mongo.db.foobar.find_one()['foo'], 'bar')

    def test_up(self):
        self.setup_migrations()

        # Remove dud migrations
        os.unlink(os.path.join(self.dir, '20101002T113000-tertiary.py'))
        os.unlink(os.path.join(self.dir, '20100901T100001-CAPITALS.py'))

        migration.up()

        h.assert_equal(migration.current_version(),
                       '20100901T103000-number-2')

        h.assert_equal(mongo.db.foobar.find_one()['foo'], 'baz')
