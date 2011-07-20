from __future__ import absolute_import

from .base import OpenSpendingCommand

class SolrCommand(OpenSpendingCommand):
    summary = "Interface to common Solr index operations."
    usage = "<subcommand> [args, ...]"
    description = """\
                  Recognized subcommands:
                    load <dataset>:       Load data for dataset into Solr
                    delete <dataset>:     Delete data for dataset from Solr
                    optimize:             Optimize the Solr index
                    clean:                Empty/reset the Solr index
                  """

    parser = OpenSpendingCommand.standard_parser()

    def command(self):
        super(SolrCommand, self).command()

        if len(self.args) < 1:
            SolrCommand.parser.print_help()
            return 1

        cmd = self.args[0]

        from openspending.lib import solr_util as solr

        if cmd == 'load':
            solr.build_index(self.args[1])
        elif cmd == 'delete':
            solr.drop_index(self.args[1])
        elif cmd == 'optimize':
            solr.optimize()
        elif cmd == 'clean':
            s = solr.get_connection()
            s.delete_query('*:*')
            s.commit()
        else:
            raise self.BadCommand("Subcommand '%s' not recognized " \
                                  "by 'solr' command!" % cmd)