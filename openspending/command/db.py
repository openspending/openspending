from __future__ import absolute_import

from .base import OpenSpendingCommand

import logging
log = logging.getLogger(__name__)

class DbCommand(OpenSpendingCommand):
    summary = "Interface to common database operations."
    usage = "<subcommand> [args, ...]"
    description = """\
                  Recognized subcommands:
                    drop:                 Drop database
                    dropcollections:      Drop collections
                    dropdataset <name>:   Drop non-shared data for dataset <name>
                    loadexample <name>:   Load test fixture <name> into database
                  """

    parser = OpenSpendingCommand.standard_parser()

    def command(self):
        super(DbCommand, self).command()

        cmd = self.args[0] if len(self.args) > 0 else None

        if cmd == 'drop':
            self._cmd_drop()
        elif cmd == 'dropcollections':
            self._cmd_dropcollections()
        elif cmd == 'dropdataset':
            self._cmd_dropdataset()
        elif cmd == 'loadexample':
            self._cmd_loadexample()
        else:
            DbCommand.parser.print_help()
            return 1

    def _cmd_drop(self):
        self._check_args_length(1)
        from openspending.mongo import drop_db
        drop_db()

    def _cmd_dropcollections(self):
        self._check_args_length(1)
        from openspending.mongo import drop_collections
        drop_collections()

    def _cmd_dropdataset(self):
        self._check_args_length(2)

        ds_name = self.args[1]

        log.warn("Dropping dataset '%s'", ds_name)

        from openspending.mongo import db

        log.info("Removing entries for dataset %s", ds_name)
        db.entry.remove({'dataset.name': ds_name})

        log.info("Removing dimensions for dataset %s", ds_name)
        db.dimension.remove({'dataset': ds_name})

        log.info("Removing distincts for dataset %s", ds_name)
        db['distincts__%s' % ds_name].drop()

        log.info("Removing cubes for dataset %s", ds_name)
        cubes = filter(lambda x: x.startswith('cubes.%s.' % ds_name),
                       db.collection_names())
        for c in cubes:
            db[c].drop()

        log.info("Removing dataset object for dataset %s", ds_name)
        db.dataset.remove({'name': ds_name})

    def _cmd_loadexample(self):
        self._check_args_length(2)
        # TODO: separate the concepts of example/development data and test
        #       fixtures.
        from openspending.ui.tests.helpers import load_fixture
        fixture_name = self.args[1]
        load_fixture(fixture_name)
