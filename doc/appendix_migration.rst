
Appendix: Migration from MongoDB to SQL-based storage
=====================================================

We've decided to move OpenSpending away from MongoDB in 0.11 and to
move back to a relational database backend, presumably supporting 
both SQLite and PostgreSQL.

The following feature requests and reasons are behind this decision:

* Better performance for in-DB aggregation queries and quasi-random
  aggregations, better analytics.
* Ease of use and deployment of OpenSpending-the-software (as opposed
  to the platform).
* Isolation of datasets in database. This is a major move that
  could be done in MongoDB as well but easily falls out of the
  larger migration.
* Support for multiple measures - also easier to implement in a 
  metadata-heavy mode of operation.

General Changes
---------------

The following fundamental aspects of the system will be changed:

* Queries will always go across several tables and generated from 
  model metadata. This is unlike the old systems where queries mostly
  ran against the entries collection and all collection names were 
  known.
* Each classifier taxonomy will have its own table constructed with
  whatever attributes (fields) apply to the dimensions in that 
  taxonomy.
* There will be a table of datasets which is independent from any 
  specific dataset and can be in a separate database. This is where 
  the model will be stored.

Examples
--------

These examples assume that a normal model file has been submitted and 
saved to the ``dataset`` table in the database, partially as columns 
on that table and in JSON serialized form.

Each dataset will have a fact table with at least these attributes::

  CREATE TABLE entry (
	  id INTEGER NOT NULL, 
	  PRIMARY KEY (id)
  );

This is equivalent to the entries collection in which each document 
used to have at least the following attributes::

  _id, entities, classifiers, dataset, _csv_import_fp, time, 
  provenance, currency

Where ``entities`` and ``classifiers`` are lists of ObjectIDs,
``dataset`` is a denormalized copy of most of the dataset record and
provenance is a nested hash of several pieces of loading information
that will have to be reproduced in the relational model in some form.

The first type of field to add to our schema will be a measure::

  "mapping": {
    [...]
    "amount": {
      "type": "measure",
      "label": "The full sum",
      "datatype": "decimal",
      "column": "amount"
      },
    [...]
    }

In MongoDB, this would have added a simple float entry to the entries
collection. The SQL representation is similarly simple::

  ALTER TABLE entry ADD COLUMN amount DECIMAL;

A dataset can also have simple attribute dimensions which are very
similar to measures::
  
  "mapping": {
    [...]
    "transaction_id": {
      "type": "value",
      "label": "Transaction ID",
      "datatype": "string",
      "column": "tx"
      },
    [...]
    }

Which will yield::

  ALTER TABLE entry ADD COLUMN transaction_id TEXT;

As well as these simple dimensions, OpenSpending also used to support
to alternative types of composite (i.e. multi-attribute dimensions):
classifiers and entities. This separation will be removed in the new 
data model, turning entities into special cases of classifiers. A 
typical classifier might look something like this::

  "mapping": {
    [...]
    "cofog1": {
      "type": "classifer",
      "taxonomy": "cofog",
      "label": "COFOG Level 1",
      "fields": [
        {"name": "name", "column": "cofog1_id", "datatype": "id"},
        {"name": "label", "column": "cofog1_label", 
                                        "datatype": "string"},
        {"name": "color", "column": "cofog1_color", 
                                        "datatype": "string"}
        ]
      },
    [...]
    }

Having a classifier on a MongoDB dataset used to have the following 
consequences:

* A new entry was added to the ``classifier`` collection for each
  distinct combination of (taxonomy, name) with each of the ``fields``
  set to its source data value and the ``taxonomy`` field added 
  from metadata.
* A denormalized copy of this classifier object was copied onto 
  each entry classified with the classifier at the dimension name 
  key.

Instead of this duplication, the SQL version will yield the following
relational schema::

  CREATE TABLE cofog (
	  id INTEGER NOT NULL,
    name TEXT NOT NULL,
    label TEXT,
    color TEXT,
	  PRIMARY KEY (id)
  );
  ALTER TABLE entry ADD COLUMN cofog1_id INTEGER;

Note that since the taxonomy name is used as a table name, model 
metadata will be required to construct queries against this schema. As
the dimension name is used for the foreign key on ``entry``, multiple
dimensions of a dataset can point at the same taxonomy.

Entities will be handled as classifiers with the taxonomy set to 
``entity`` (and thus in the table ``entity``). 

To further illustrate this, here is a query to generate a full view of 
the entries in a test dataset (see spendb unit tests) with all dimensions 
joined to the facts table::

  SELECT function.id AS function_id, function.name AS function_name, 
         function.label AS function_label, entry.field AS entry_field, 
         "to".id AS to_id, "to".name AS to_name, "to".label AS to_label, 
         "to".const AS to_const, entry.time AS entry_time, 
         entry.amount AS entry_amount 
  FROM test_entry AS entry 
    JOIN test_funny AS function ON function.id = entry.function_id 
    JOIN test_entity AS "to" ON "to".id = entry.to_id 
  WHERE 1=1

Note that the tables in this example have been prefixed with the dataset
name. In PostgreSQL, schemata can be used instead.

Further, this is an aggregation query that generates output to satify the 
simple cubes API used by all visualizations running on OpenSpending::

  SELECT sum(entry.amount) AS amount, count(entry.id) AS entries, 
         function.id AS function_id, function.name AS function_name, 
         function.label AS function_label, entry.field AS entry_field 
  FROM test_entry AS entry 
    JOIN test_funny AS function ON function.id = entry.function_id 
  GROUP BY function.id, entry.field 
  ORDER BY amount desc

This might have to be INSERTED into a cache table without filters applied
in order to accelerate drilldowns over very large datasets (or memoized in
the application).

