from setuptools import setup, find_packages
from openspending.ui import __version__

setup(
    name='openspending',
    version=__version__,
    description='OpenSpending',
    author='Open Knowledge Foundation',
    author_email='okfn-help at lists okfn org',
    url='http://github.com/okfn/openspending',

    install_requires=[
        "WebOb==1.0.8", # Explicitly specify WebOb 1.0.8, as with 1.1
                        # integration with Pylons is broken:
                        # see https://gist.github.com/1214075
        "Pylons==1.0",
        "Genshi==0.6",
        "pymongo==1.11",
        "repoze.who==2.0b1",
        "repoze.who-friendlyform==1.0.8",
        "Unidecode==0.04.7",
        "python-dateutil==1.5",
        "solrpy==0.9.4",
        "pyutilib.component.core==4.3.1",
        "Babel==0.9.6",
        "colander==0.9.3",
        "distribute>=0.6.10",
        "mock==0.7.2",
        "sphinx==1.0.7",
        "argparse==1.2.1"
    ],
    setup_requires=[
        "PasteScript==1.7.4.2",
        "nose==1.1.2"
    ],

    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['openspending', 'openspending.plugins'],

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
    }
)
