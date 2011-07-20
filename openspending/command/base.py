import os
import logging

from paste.deploy import appconfig
from paste.script import command

from openspending.ui.config.environment import load_environment

# Monkeypatch Paste's version of OptionParser to prevent it munging newlines
# in command descriptions
command.optparse.OptionParser.format_description = lambda self, d: self.description

log = logging.getLogger('openspending')

class OpenSpendingCommand(command.Command):
    group_name = 'openspending'

    @classmethod
    def standard_parser(cls, *args, **kwargs):
        parser = command.Command.standard_parser(*args, **kwargs)
        parser.add_option('-c', '--config', dest='config',
                          default='development.ini', metavar='PATH',
                          help='Config file to use [$REPO_ROOT/development.ini].')
        return parser

    def command(self):
        self._load_config()

        # With default log level set to WARN, this gives -v == INFO, -vv == DEBUG
        log.setLevel(max(10, log.getEffectiveLevel() - 10 * self.options.verbose))

    def _load_config(self):
        config_file = self.options.config
        self.logging_file_config(config_file)

        here_dir = os.getcwd()
        conf = appconfig('config:' + config_file, relative_to=here_dir)
        load_environment(conf.global_conf, conf.local_conf)

    def _check_args_length(self, n):
        if len(self.args) != n:
            self.__class__.parser.print_help()
            raise self.BadCommand('\nWrong number of arguments: see usage message above!')
