from __future__ import absolute_import

import logging

from .base import OpenSpendingCommand

log = logging.getLogger(__name__)

class RemoveEntriesCommand(OpenSpendingCommand):
    summary = "Delete all entries associated with a dataset"
    usage = "<dataset>"

    parser = OpenSpendingCommand.standard_parser()

    def command(self):
        super(RemoveEntriesCommand, self).command()
        self._check_args_length(1)

        from openspending.model import Entry

        log.info("Deleting all entries in dataset: %s" % dataset_name)
        errors = Entry.c.remove({"dataset.name": self.args[0]})
        log.info("Errors: %s" % errors)
