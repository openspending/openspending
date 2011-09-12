from __future__ import absolute_import

from .base import OpenSpendingCommand

# TODO: generalise
class GrantAdminCommand(OpenSpendingCommand):
    summary = "Grant admin access to given user."
    usage = "<username>"

    parser = OpenSpendingCommand.standard_parser()

    def command(self):
        super(GrantAdminCommand, self).command()
        self._check_args_length(1)

        from openspending.model import account

        username = self.args[0]
        a = account.find_one_by('name', username)

        if a is None:
            print "Account `%s' not found." % username
            return False

        account.add_role(a, 'admin')
