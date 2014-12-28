import os
from setuptools import setup, find_packages


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
    version='0.17',
    description='OpenSpending',
    author='Open Knowledge Foundation',
    author_email='openspending-dev at lists okfn org',
    url='http://github.com/openspending/openspending',
    install_requires=[
    ],
    setup_requires=[],

    packages=filter(package_filter, find_packages()),
    namespace_packages=['openspending'],
    package_data={
        'openspending': (
            files_in_pkgdir('openspending', 'static') +
            files_in_pkgdir('openspending', 'templates')
        )
    },
    test_suite='nose.collector',

    zip_safe=False,

    entry_points={
        'console_scripts': [
            'ostool = openspending.command:main',
            'openspending = openspending.command:main'
        ]
    },

    message_extractors={
        'openspending': [('**.py', 'python', None),
                         ('templates/**.html', 'jinja2', None),
                         ('static/**', 'ignore', None),
                         ]
        },
)
