Installation and Setup
======================

Requirements
'''''''''''''

* Python_ >= 2.7, with pip_ and virtualenv_   
* PostgreSQL_ >= 8.4
* `Apache Solr`_

.. _Python: http://www.python.org/
.. _PostgreSQL: http://www.postgres.org/
.. _Apache Solr: http://lucene.apache.org/solr/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pypi.python.org/pypi/pip

Installation
''''''''''''

First, check out the source code from the repository, e.g. via git on 
the command line::

    $ git clone http://github.com/okfn/openspending.git
    $ cd openspending

We also highly recommend you use a virtualenv_ to isolate the installed 
dependencies from the rest of your system.::

    $ virtualenv --no-site-packages ./pyenv

Now activate the environment. Your prompt will be prefixed with the name of
the environment.::

    $ source ./pyenv/bin/activate

Ensure that any in shell you use to complete the installation you have run the 
preceding command.

Having the virtualenv set up, you can install OpenSpending and its dependencies.
This should be pretty painless. Just run::

    $ pip install -e . -r ./pip-requirements.txt


Setup Solr
''''''''''

Create a configuration home directory to use with Solr. This is most easily 
done by copying the Solr example configuration from the `Solr tarball`_, and 
replacing the default schema with one from OpenSpending.::

    $ cp -R apache-solr-3.1.0/example/solr/* ./solr
    $ ln -sf "../wdmmg_schema.xml" ./solr/conf/schema.xml

.. _Solr tarball: http://www.apache.org/dyn/closer.cgi/lucene/solr/

Start Solr with the full path to the folder as a parameter: ::

    $ solr $(pwd)/solr


Customize the configuration file
''''''''''''''''''''''''''''''''

Create a configuration file, choosing a name that reflects the environment
in which this deployment will be used. For a development environment:::

    $ cp development.ini_tmpl development.ini

Edit the config file with relevant details for your local machine. The
options in the file are commented. Some of the important options in 
`[app:main]` are::
    
    # Configure your database. e.g. for a development database:
    openspending.db.url = postgresql://user:pass@host/dbname
    
    # Configure your Solr url. This is a typical default:
    openspending.solr.url = http://localhost:8983/solr
    
    # Choose which plugins to activate:
    openspending.plugins = treemap datatables [...]
    

Test the install and run the site
---------------------------------

Create test configuration (which inherits, by default, from `development.ini`): ::

    $ cp test.ini_tmpl test.ini

Run the tests.::

    $ nosetests 

Finally, run the site from development.ini::

    $ paster serve --reload development.ini

Create an Admin User
--------------------

On the web user interface, register as a normal user. Once signed up, go into 
the database and do (replacing your-name with your login name)::

  UPDATE "account" SET admin = true WHERE "name" = 'username';

