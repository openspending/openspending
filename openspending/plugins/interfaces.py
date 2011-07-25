"""
Interfaces for plugins system
See doc/plugins.rst for more information
"""

from inspect import isclass
from pyutilib.component.core import Interface as _pca_Interface

class Interface(_pca_Interface):

    @classmethod
    def provided_by(cls, instance):
        return cls.implemented_by(instance.__class__)

    @classmethod
    def implemented_by(cls, other):
        if not isclass(other):
            raise TypeError("Class expected", other)
        try:
            return cls in other._implements
        except AttributeError:
            return False


class IRoutes(Interface):
    """
    Plugin into the setup of the routes map creation.

    """
    def before_map(self, map):
        """
        Called before the routes map is generated. ``before_map`` is before any
        other mappings are created so can override all other mappings.

        :param map: Routes map object
        """

    def after_map(self, map):
        """
        Called after routes map is set up. ``after_map`` can be used to add fall-back handlers.

        :param map: Routes map object
        """


class IRequest(Interface):
    """
    Plugin into the lifecycle of a request.
    """
    def before(self, request, tmpl_content):
        """
        Called before the request is processed.
        """

    def after(self, request, tmpl_context):
        """
        Called after the request is processed.
        """


class IGenshiStreamFilter(Interface):
    '''
    Hook into template rendering.
    See openspending.ui.lib.base.py:render
    '''

    def filter(self, stream):
        """
        Return a filtered Genshi stream.
        Called when any page is rendered.

        :param stream: Genshi stream of the current output document
        :returns: filtered Genshi stream
        """
        return stream


class IDatasetController(Interface):
    """ Set controller variables for datasets. """

    def index(self, c, request, response, query):
        return query

    def read(self, c, request, response, entity):
        pass


class IEntryController(Interface):
    """ Set controller variables for entries. """

    def index(self, c, request, response, query):
        return query

    def read(self, c, request, response, entity):
        pass


class IEntityController(Interface):
    """ Set controller variables for entities. """

    def index(self, c, request, response, query):
        return query

    def read(self, c, request, response, entity):
        pass


class IClassifierController(Interface):
    """ Set controller variables for classifiers. """

    def index(self, c, request, response, query):
        return query

    def read(self, c, request, response, entity):
        pass


class ISolrSearch(Interface):
    """ Set controller variables for classifiers. """

    def update_index(self, entity):
        return entity


class IConfigurable(Interface):
    """
    Pass configuration to plugins and extensions
    """

    def configure(self, config):
        """
        Called by load_environment
        """


class IConfigurer(Interface):
    """
    Modify the configuration on the fly.
    """

    def configure(self, config):
        """
        Called by load_environment
        """


class IMiddleware(Interface):
    """Modify the app middleware stack."""

    def configure(self, app):
        """Called by ``openspending.ui.config.middleware:make_app``"""
        return app
