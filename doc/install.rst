OpenSpending Installation and setup
===================================

Prerequisites
'''''''''''''

* Python_ >= 2.6, with pip_ and virtualenv_   
* PostgreSQL_ >= 8.4
* `Apache Solr`_
                
.. _Python: http://www.python.org/
.. _PostgreSQL: http://www.postgres.org/
.. _Apache Solr: http://lucene.apache.org/solr/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pypi.python.org/pypi/pip

Introduction
''''''''''''

To simplify the rest of this document, please first change directory to the 
root of the `wdmmg` repository.

Use a virtualenv!
'''''''''''''''''

For an installation we highly recommend you use a virtualenv_ environment. ::

    $ virtualenv --no-site-packages ./pyenv

Now activate the environment. Your prompt will be prefixed with the name of
the environment. ::

    $ source ./pyenv/bin/activate

Ensure that any in shell you use to complete the installation you have run the 
preceding command.

Install OpenSpending and related packages
'''''''''''''''''''''''''''''''''''''''''

This should be pretty painless. Just run::

    $ pip install -e . -r ./pip-requirements.txt

In a development environment, you will almost certainly need the `wdmmg-ext`
package, for importing datasets: ::

    $ pip install -e hg+ssh://hg@bitbucket.org/okfn/wdmmg-ext#egg=wdmmg-ext

Create and customize a configuration file
'''''''''''''''''''''''''''''''''''''''''

Create a configuration file, choosing a name that reflects the environment
in which this deployment will be used. For a development environment:::

    $ paster make-config wdmmg ./development.ini

Edit the config file with relevant details for your local machine. The
options in the file are commented. Some of the important options in 
`[app:main]` are::
    
    # Configure your MongoDB database. e.g. for a development database:
    openspending.db.url = postgresql://user:pass@host/dbname
    
    # Configure your Solr url. This is a typical default:
    openspending.solr.url = http://localhost:8983/solr
    
    # Choose which plugins to activate:
    openspending.plugins = treemap datatables [...]
    

Setup Solr
''''''''''

Create a configuration home directory to use with Solr. This is most easily 
done by copying the Solr example configuration from the `Solr tarball`_, and 
replacing the default schema with one from OpenSpending. ::           

    $ cp -R apache-solr-3.1.0/example/solr/* ./solr
    $ ln -sf "../wdmmg_schema.xml" ./solr/conf/schema.xml
                                                                      
.. _Solr tarball: http://www.apache.org/dyn/closer.cgi/lucene/solr/

Start Solr with the full path to the folder as a parameter: ::
  
    $ solr $(pwd)/solr

Setup Celery
''''''''''''

Celery_ is used to manage job queues for background tasks. It is installed
automatically as a dependency of `wdmmg`. You can find several `celery*` commands
in your virtualenv's /bin directory. 
                                                                                                                                                           
Adapt `celeryconfig.py` to your needs. The default configuration uses MongoDB
as a storage and queue backend. To use another python module to configure 
celery, specify it in your pylons config under the key `celery_config`. e.g. to 
use a module called `celeryconfig_production` put the following in your Pylons 
config file: ::

    celery_config = celeryconfig_production

To run a celery command in the OpenSpending Pylons environment, you have to 
run it like so: ::

    paster celeryd development.ini#wdmmg.config.environment.load_environment

The part before the hash is the configuration you want to use, the part after 
the hash is the import path to the function that loads the OpenSpending Pylons 
environment.

.. _Celery: http://celeryproject.org/

Test the installation
---------------------

Create test configuration (which inherits, by default, from `development.ini`): ::

    $ cp test.example.ini test.ini

Run the tests.::

    $ nosetests 


Run the site
------------

Finally, run the site from development.ini::

  (env)/path/to/env/openspending$ paster serve --reload development.ini

Create an Admin User
--------------------

  * Register
  * Go into the database and do (replacing your-name with your login name)::
    
    UPDATE "account" SET admin = true WHERE "name" = 'username';

