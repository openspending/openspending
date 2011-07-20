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

        from openspending.model.account import Account

        username = self.args[0]
        account = Account.by_name(username)

        if account is None:
            print "Account `%s' not found." % username
            return False

        roles = set(account["_roles"])

        roles |= set([u'admin'])
        account["_roles"] = list(roles)

        Account.save(account)