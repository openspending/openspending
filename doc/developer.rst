Developer Documentation
=======================

Creating a DB Migration
'''''''''''''''''''''''

1. Make sure you're in the virtualenv for OpenSpending and run ``migrate script
   "<description>" migration``. Replace ``<description>`` with a description
   for your change. For instance, "Add terms column".
2. A new file will be created in ``migration/versions``. The output of
   ``migrate`` will have the filename for it.
3.  Edit the file and add migration commands.  Look into `sqlalchemy-migrate
    documentation
    <https://sqlalchemy-migrate.readthedocs.org/en/latest/versioning.html#making-schema-changes>`_
    or other migrations in ``migration/versions`` for help on how to write
    a migration.
4. Once you're done writing the migration, run it with ``ostool db migrate``.


Creating and running tests
''''''''''''''''''''''''''

We strive to test all functionality in OpenSpending. If you add a new
functionality to the code base, please take the time to create a test for it.
We regression test everything that is contributed into the code base.

If tests need to be removed or modified as part of a code contributions, please
indicate so clearly in the relevant commit, preferably using ALL CAPS in the
first line of the commit message.

All tests can be found in ``openspending.tests``, arranged into directories by
what part of openspending they test:

- ``command``: Tests for ``ostool`` functionality (code in 
  ``openspending.command``)
- ``views``: Tests for user facing functionality (access points via URLs)
   as OpenSpending follows an MVC (model, view, controller) architecture (code
   in ``openspending.views`` with templates in ``templates``).
- ``importer``: Tests for the CSV importer in OpenSpending, the important bit
  handled by ``Celery`` to get data into OpenSpending (code in
  ``openspending.importer`` which is called from ``openspending.tasks`` which
  calls ``openspending.command``).
- ``lib``: Tests generic openspending functions and classes made designed to
  be reusable all over the code base. These include solr wrappers, parameter
  parsers and views (code in ``openspending.lib``).
- ``model``: Tests for the database model functionality (the database
  interface) as OpenSpending follows an MVC architecture (code in
  ``openspending.model``).

Test cases should inherit from the Test classed made available in
``openspending.tests.base``:

- ``TestCase``: Tests for functionality without touching the database
- ``DatabaseTestCase``: Tests that need to test database interactions
- ``ControllerTestCase``: Tests that need to test HTTP interactions

In ``openspending.tests.helpers`` a few functions are made available that can
make tests easier to write. Noteworthy functions are ``make_account`` to make
a user account to test with, ``load_fixture`` to load a test dataset into the
test database, ``clean_and_reindex_solr`` to ensure any solr tests are clean
and isolated. There are other test helper functions in
``openspending.tests.helpers`` and test case writers are encouraged to take a
look at the test helpers file.

Test datasets are available in the fixtures directory, both models and data.
These are loaded in via the ``load_fixture`` function in
``openspending.tests.helpers``.

Run the OpenSpending test suite by running

    nosetests

in the root of the repository, while in an active virtualenv.
