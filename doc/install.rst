Installation and Setup
======================


Simple install
''''''''''''''

Requirements
------------

* Vagrant_ >= 1.4

Installation
------------

You can avoid installing OpenSpending on your development machine by using Vagrant_ to execute the application and all of its dependencies in a virtual machine. To make use of this option, make sure to install Vagrant and the included VirtualBox provider. 

If you haven't already, you'll need to install Vagrant's `cachier` plugin:

    $ vagrant plugin install vagrant-cachier

Then, from the source repository, you can set up a VM with::

    $ vagrant up

This will run for a while (fetch a coffee), until a working VM with Ubuntu 13.04 and OpenSpending has been deployed. Once the application has run, you can run OpenSpending within the VM::

    $ vagrant ssh
    vagrant@openspending$ cd /vagrant
    vagrant@openspending$ paster serve --reload vagrant.ini 

The virtual machine includes OpenSpending, Postgres, RabbitMQ and Solr.

.. _Vagrant: http://vagrantup.com/


Manual install
''''''''''''''

Requirements
------------

* Python_ >= 2.7, with pip_ and virtualenv_   
* PostgreSQL_ >= 8.4
* RabbitMQ_ >= 2.6.1
* `Apache Solr`_ >= 4.0.0

.. _Python: http://www.python.org/
.. _PostgreSQL: http://www.postgres.org/
.. _RabbitMQ: http://www.rabbitmq.com//
.. _Apache Solr: http://lucene.apache.org/solr/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pypi.python.org/pypi/pip

Installation
------------

First, check out the source code from the repository, e.g. via git on 
the command line::

    $ git clone http://github.com/openspending/openspending.git
    $ cd openspending

We also highly recommend you use a virtualenv_ to isolate the installed 
dependencies from the rest of your system.::

    $ virtualenv ./pyenv --distribute

Now activate the environment. Your prompt will be prefixed with the name of
the environment.::

    $ source ./pyenv/bin/activate

Ensure that any in shell you use to complete the installation you have run the 
preceding command.

Having the virtualenv set up, you can install OpenSpending and its dependencies.
This should be pretty painless. Just run::

    $ pip install -r requirements.txt -e .

Additionally to the core repository, you will need to check out two auxilliary
repositories and symlink them into OpenSpending. The repos contain the 
JavaScript components and the help system content for the site. The following 
instructions will download and link in the JS files::

    $ git clone http://github.com/openspending/openspendingjs.git
    $ ln -s <full path to openspendingjs> openspending/ui/public/static/openspendingjs

You will also need to install python bindings for your database. For example,
for Postgresql you will want to install the psycopg2 library::

    $ pip install psycopg2

Create a database if you do not have one already. We recommend using Postgres
but you can use anything compatible with SQLAlchemy. For postgres you would do::

    $ createdb -E utf-8 --owner {your-database-user} openspending

Having done that, you can copy configuration templates::

    $ cp development.ini_tmpl development.ini

Edit the configuration files to make sure you're pointing to a valid database 
URL is set::

    # TCP
    openspending.db.url = postgresql://{user}:{pass}@localhost/openspending

    or

    # Local socket
    openspending.db.url = postgresql:///openspending

Initialize the database::

    $ ostool development.ini db init

Generate the help system documentation (this is used by the front-end
and must be available, developer documents are separate). The output 
will be copied to the web applications template directory::

    $ git submodule init && git submodule update
    $ (cd doc && make clean html)

Compile the translations:

    $ python setup.py compile_catalog

Run the application::

    $ paster serve --reload development.ini

In order to use web-based importing and loading, you will also need to set up
the celery-based background daemon. When running this, make sure to have an
instance of RabbitMQ installed and running and then execute::

    $ celery -A openspending.tasks -p development.ini worker

You can validate the functioning of the communication between the backend and
frontend components using the ping action::

    $ curl -q http://localhost:5000/__ping__ >/dev/null

This should result in "Pong." being printed to the background daemon's console.

Setup Solr
----------

Create a configuration home directory to use with Solr. This is most easily 
done by copying the Solr example configuration from the `Solr tarball`_, and 
replacing the default schema with one from OpenSpending.::

    $ cp -R apache-solr-<version>/* ./solr/
    $ ln -sf <full path to openspending>/solr/openspending_schema.xml ./solr/example/solr/collection1/conf/schema.xml

.. _Solr tarball: http://www.apache.org/dyn/closer.cgi/lucene/solr/

Start Solr with the full path to the folder as a parameter: ::

    $ (cd solr/example && java -Dsolr.velocity.enabled=false -jar start.jar)

Test the install
----------------

Create test configuration (which inherits, by default, from `development.ini`): ::

    $ cp test.ini_tmpl test.ini

You will need to either set up a second instance of solr, or comment
out the solr url in test.ini so that the tests use the same instance
of solr. Regrettably, the tests delete all data from solr when they
run, so having them share the development instance may be
inconvenient.

Run the tests.::

    $ nosetests 

Import a sample dataset: ::

    $ ostool development.ini csvimport --model https://dl.dropbox.com/u/3250791/sample-openspending-model.json http://mk.ucant.org/info/data/sample-openspending-dataset.csv
    $ ostool development.ini solr load openspending-example

Verify that the data is visible at http://127.0.0.1:5000/openspending-example/entries

Create an Admin User
--------------------

On the web user interface, register as a normal user. Once signed up, go into 
the database and do (replacing your-name with your login name)::

  UPDATE "account" SET admin = true WHERE "name" = 'username';

