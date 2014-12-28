from flask.ext.script import Manager


def create_submanager(**opts):
    def sub_opts(**kwargs):
        pass
    mgr = Manager(sub_opts, **opts)
    mgr.__doc__ = opts.get('description')
    return mgr


class CommandException(Exception):
    pass
