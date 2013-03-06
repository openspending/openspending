Developer Documentation
=======================

This section aims to provide developers to the OpenSpending platform with
instuctions on how to do tasks that are commonly performed.

Creating a DB Migration
'''''''''''''''''''''''

1. Make sure you're in the virtualenv for openspending and run ``migrate script
   "<description>" migration``. Replace ``<description>`` with a description
   for your change. For instance, "Add terms column".
2. A new file will be created in ``migration/versions``. The output of
   ``migrate`` will have the filename for it.
3.  Edit the file and add migration commands.  Look into `sqlalchemy-migrate
    documentation
    <https://sqlalchemy-migrate.readthedocs.org/en/latest/versioning.html#making-schema-changes>`_
    or other migrations in ``migration/versions`` for help on how to write
    a migration.
4. Once you're done writing the migration, run it with ``ostool development.ini
   db migrate``.
