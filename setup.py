import os
from setuptools import setup, find_packages

from openspending.version import __version__

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
    if pkg in ['openspending.test', 'openspending.test.helpers']:
        return True
    elif (pkg.startswith('openspending.test') or
          pkg.startswith('openspending.ui.test')):
        return False
    else:
        return True

setup(
    name='openspending',
    version=__version__,
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
        ],
        'paste.global_paster_command': [
            'celeryd=openspending.command.celery:CeleryDaemonCommand',
        ]
    },

    message_extractors = {'openspending': [
            ('**.py', 'python', None),
            ('ui/public/**', 'ignore', None),
            ]},
)
