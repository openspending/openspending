# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)


import warnings
warnings.filterwarnings('ignore', 'Options will be ignored.')

# Silence SQLAlchemy warning:
import warnings
warnings.filterwarnings(
    'ignore',
    'Unicode type received non-unicode bind param value.')
