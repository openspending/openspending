import os
os.environ['CELERY_LOADER'] = 'openspending.command.celery.loader.PylonsLoader'

import os
from paste.script.command import Command, BadCommand
from openspending.command import _configure_pylons

__all__ = ['CeleryDaemonCommand']

class CeleryCommand(Command):
    """
    Abstract Base Class for celery commands.

    The celery commands are somewhat aggressive about loading
    celery.conf, and since our module sets the `CELERY_LOADER`
    environment variable to our loader, we have to bootstrap a bit and
    make sure we've had a chance to load the pylons config off of the
    commandline, otherwise everything fails.
    """
    min_args = 1
    min_args_error = "Please provide a paster config file as an argument."
    takes_config_file = 1
    requires_config_file = True

    def run(self, args):
        """
        Overrides Command.run

        Checks for a config file argument and loads it.
        """
        if len(args) < self.min_args:
            raise BadCommand(
                self.min_args_error % {'min_args': self.min_args,
                                       'actual_args': len(args)})
        # Decrement because we're going to lob off the first argument.
        # @@ This is hacky
        self.min_args -= 1
        self.bootstrap_config(args[0])
        self.update_parser()
        return super(CeleryCommand, self).run(args[1:])

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """
        raise NotImplemented("Abstract Method.")

    def bootstrap_config(self, conf):
        """
        Loads the pylons configuration.
        """
        path_to_ini_file = os.path.realpath(conf)
        _configure_pylons(path_to_ini_file)


class CeleryDaemonCommand(CeleryCommand):
    """Start the celery worker

    Starts the celery worker that uses a paste.deploy configuration
    file.
    """
    usage = 'CONFIG_FILE [celeryd options...]'
    summary = __doc__.splitlines()[0]
    description = "".join(__doc__.splitlines()[2:])

    parser = Command.standard_parser(quiet=True)

    def update_parser(self):
        from celery.bin.celeryd import WorkerCommand
        w = WorkerCommand()
        for x in w.get_options():
            self.parser.add_option(x)

    def command(self):
        from celery.apps import worker
        return worker.run_worker(**vars(self.options))

