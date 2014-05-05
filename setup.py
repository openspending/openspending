import os
import re
from setuptools import setup, find_packages


def get_version():
    """
    Parse the version from the openspending version file.
    This is Zooko's method for getting the version into
    setup.py without having to execute the file or import
    an pacakge that hasn't been set up (since it is being
    set up as part of running setup.py)
    """

    # Define version file, we define our version in
    # openspending._version and read the file
    VERSIONFILE = "openspending/_version.py"
    verstrline = open(VERSIONFILE, "rt").read()

    # Parse the file to find the line that defines the version
    # using a regular expression
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)

    # If we find a match we can return the version (group 1)
    # if not we raise an error
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError(
            "Unable to find version string in %s." % (VERSIONFILE,))

PKG_ROOT = '.'


def files_in_pkgdir(pkg, dirname):
    pkgdir = os.path.join(PKG_ROOT, *pkg.split('.'))
    walkdir = os.path.join(pkgdir, dirname)
    walkfiles = []
    for dirpath, _, files in os.walk(walkdir):
        fpaths = (os.path.relpath(os.path.join(dirpath, f), pkgdir)
                  for f in files)
        walkfiles += fpaths
    return walkfiles


def package_filter(pkg):
    """
    Filter packages so that we exclude test cases but include regular test
    objects available in openspending.tests' modules (all test cases are
    in subdirectories).
    """

    # We want to include openspending.tests but not its subpackages
    # Hence we only check for things starting with openspending.tests.
    # (note the trailing period to denote subpackages)
    return not pkg.startswith('openspending.tests.')

setup(
    name='openspending',
    version=get_version(),
    description='OpenSpending',
    author='Open Knowledge Foundation',
    author_email='okfn-help at lists okfn org',
    url='http://github.com/okfn/openspending',
    install_requires=[
    ],
    setup_requires=[
        "PasteScript==1.7.5",
        "nose==1.1.2"
    ],

    packages=filter(package_filter, find_packages()),
    namespace_packages=['openspending'],
    package_data={
        'openspending.ui': (
            files_in_pkgdir('openspending.ui', 'public') +
            files_in_pkgdir('openspending.ui', 'templates')
        )
    },
    test_suite='nose.collector',

    zip_safe=False,

    paster_plugins=['PasteScript', 'Pylons'],

    entry_points={
        'paste.app_factory': [
            'main = openspending.ui.config.middleware:make_app'
        ],
        'paste.app_install': [
            'main = pylons.util:PylonsInstaller'
        ],
        'console_scripts': [
            'ostool = openspending.command:main'
        ]
    },

    message_extractors={
        'openspending': [('**.py', 'python', None),
                         ('ui/alttemplates/**.html', 'jinja2', None),
                         ('ui/public/**', 'ignore', None),
                         ]
        },
)
