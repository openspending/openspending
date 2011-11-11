Deployment practices
====================

The target platform of OpenSpending is Ubuntu Lucid Lynx (10.04) LTS. While
the software can be installed on other systems (OS X is used on a daily 
basis, Windows may be a stretch), the following guide will refer to 
dependencies by their Ubuntu package name.

Jetty-based multi-core Solr
'''''''''''''''''''''''''''

Under Ubuntu, you can install Solr (with a Jetty-based runtime container) 
from a package::

  # apt-get install solr-jetty

After installing it, edit ``/etc/default/jetty`` and set ``NO_START`` to 0.
If your backend and frontend systems are separated, also bind Jetty to an
external interface using the ``JETTY_HOST`` variable. Finally, you can 
increase the Java runtime heap memory limit by setting the ``-Xmx`` flag in
``JAVA_OPTIONS`` to a higher value, e.g. 4G.

Solr will store its index configuration in ``/usr/share/solr``, which has a
symlink called ``conf`` that points to ``/etc/solr/conf``. 

If you want to put Solr into multi-core mode (e.g. to run two instances of 
OpenSpending or to share the Solr install with another service), remove the 
symlink and create a set of folders named after the cores you need, e.g. 
``/usr/share/solr/openspending.org``. Drop a copy of the ``conf`` directory 
into this folder and edit the contained ``solrconfig.xml`` so that the 
``<dataDir>`` points at a path that is specific to this core. 

Remove the included ``schema.xml`` and replace it with a symlink to 
``solr/openspending_schema.xml`` file in the source repository. Finally, 
create a file called ``solr.xml`` in ``/usr/share/solr`` with the following 
contents::

  <solr persistent="true" sharedLib="lib">
    <cores adminPath="/admin/cores">
      <core name="openspending.org" instanceDir="openspending.org" />
    </cores>
  </solr>

Then, restart Jetty to make the changes take effect::

  # /etc/init.d/jetty stop; /etc/init.d/jetty start


Installing the software
'''''''''''''''''''''''

This guide is intended as a complement to :doc:`install`, so a basic
familiarity with the installation procedure and configuration options is
assumed. The key differences in a production install are these:

* We usually install OpenSpending as user ``okfn`` in ``~/var/srvc/<site>``,
  where the installation root is a ``virtualenv``.
* As a database, we'll always use PostgreSQL (version 8.4 for production).
  This also means we need to install the ``psycopg2`` python bindings used
  by SQLALchemy. The server is installed and set up by creating a user and 
  initial database::
    
    # apt-get install postgres
    # su postgres
    $ createuser -D -P -R -S openspending
    Password:
    $ createdb -E utf8 -O openspending -T template0 openspending.org

* To install the core software and dependencies, a pip file is created as
  ``pip-site.txt`` with the following contents::

    psycopg2
    gunicorn
    -e git+http://github.com/okfn/openspending#egg=openspending
    -e git+http://github.com/okfn/openspending.etl#egg=openspending.etl
    -e git+http://github.com/okfn/openspending.plugins.treemap#egg=openspending.plugins.treemap
    -e git+http://github.com/okfn/openspending.plugins.datatables#egg=openspending.plugins.datatables

  This means that updates can be installed easily and quickly by running
  the same command used for the initial setup::

    (env)~/var/srvc/openspending.org$ pip install -r pip-site.txt

* The application is run through ``gunicorn`` (Green Unicorn), a fast, 
  pre-fork based HTTP server for WSGI applications. The application provides
  special support for pastescript so that it can be started via a simple
  prompt::

    (env)~/var/srvc/openspending.org$ gunicorn_paster site.ini

  (Where site.ini is your primary configuration file.) To determine the 
  number of workers and the port to listen on, a configuration file called
  ``gunicorn.py`` is created with basic settings::

    import multiprocessing
    bind = "127.0.0.1:18000"
    workers = multiprocessing.cpu_count() * 2 + 1

  This can be passed using the ``-c`` argument::

    (env)~/var/srvc/openspending.org$ gunicorn_paster -c gunicorn.py site.ini

* In order to make sure gunicorn is automatically started, monitored, and run
  with the right arguments, ``supervisord`` is installed::

    # apt-get install supervisor

  After installing supervisor, a new configuration file can be dropped into 
  ``/etc/supervisor/conf.d/openspending.org.conf`` with the following basic
  contents::

    [program:openspending.org]
    command=/home/okfn/var/srvc/openspending.org/bin/gunicorn_paster /home/okfn/var/www/openspending.org/site.ini -c /home/okfn/var/srvc/openspending.org/gunicorn.py
    directory=/home/okfn/var/srvc/openspending.org/
    user=www-data
    autostart=true
    autorestart=true
    stdout_logfile=/home/okfn/var/srvc/openspending.org/logs/supervisord.log
    redirect_stderr=true

  For logging, this required that you create the logs directory in the site 
  install, with permissions for ``www-data`` to write it.

  Supervisor can be started as a daemon::

    # /etc/init.d/supervisor start

* Finally, ``nginx`` is used as a front-end web server through which the
  application is proxied and static files are served. Install ``nginx`` as 
  a normal package::

    # apt-get install nginx

  A configuration can be created at ``/etc/nginx/sites-available/openspending``
  and later symlinked over into the ``sites-enabled`` folder. The host will 
  contain a server name, static path and a reference to the upstream
  ``gunicorn`` server::

      upstream app_server {
        server 127.0.0.1:18000;
      }

      server {
        listen 80;
        server_name openspending.org;

	    access_log /var/log/nginx/openspending.org-access.log;
        error_log /var/log/nginx/openspending.org-error.log debug;

        root /home/okfn/var/srvc/openspending.org/src/openspending/openspending/ui/public;

	    location /static {
          alias /home/okfn/var/srvc/openspending.org/src/openspending/openspending/ui/public/static;
        }

        location / {
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header Host $http_host;
          proxy_redirect off;
          proxy_pass http://app_server;
          break;
        }
      }

  In a completely unexpected turn of events, ``nginx`` can be started 
  as a daemon::

    # /etc/init.d/nginx start


