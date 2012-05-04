Domain Model Design
===================

The following documentations aims to outline the way in which OpenSpending 
stores and queries data. Note that this documentation is aimed at developers
who want to modify core functions of the platform. For anyone who wants to 
simply load data or use publicly accessible APIs, online help is provided 
from within the application.

.. _olap-intro:

Offline analytics in OpenSpending
---------------------------------

OpenSpending provides a multi-tenant OLAP-style data store, a concept sometimes
referred to as a *data mart*. The system aims to allow the addition of further 
datasets at run-time and via the web, while keeping loaded data immutable. For
each dataset, a reference is managed within the core data model, and a specific 
model (i.e. a set of tables) is generated to keep the actual data.

The generated data model usually represents a *star schema* representation of 
some set of financial transactions. In a star schema, each individual *entry* 
(i.e. each transaction) is stored in a core table, the *fact table*. This fact
table may have two types of attributes: *measures* and *dimensions*. Measures
describe the actual values of the entry - in the case of OpenSpending, this is
some financial unit. Dimensions serve to augument these facts with explanatory
information, e.g. the time of the transaction, the spender, recipient, IDs, 
descriptions and classifications that can be applied to the data.

Unlike most OLAP systems, OpenSpending knows two different types of dimensions:
attribute dimensions and compound dimensions. While attribute dimensions only
keep a single value, compound dimensions store multiple attributes (e.g. the 
name, address and vat ID of a supplier who recieves funds).

When querying the data, one can either access indiviudal entries or run 
*aggregations* which sum up the measures based on some criterion. Two types of
criteria supported in OpenSpending are *cuts* and *drilldowns*. Cuts reduce 
the set of aggregated entries by applying some filter criterion to a set of 
dimensions of each entry (e.g. one can only include the spending in a single
year). Drilldowns, instead of generating a single sum, calculate the sum for 
each value of a dimension individually (e.g. each year's spending is calculated
seperately).


Modeling/mapping schema
-----------------------

OpenSpending keeps an extensive set of metadata for each :py:class:`~.Dataset`. 
The metadata is used to create the physical model, query the generated data 
structures, pre-define reports (views) to run off the data and provide general 
information about the dataset.

The metadata is stored in a specfied object structure, which is often 
represented as JSON. The basic layout is this::

  "dataset": {
    ... basic dataset attributes ...
    },
  "mapping": {
    ... dimension descriptions ...
    },
  "views": [
    ... pre-defined views ...
    ]

Each of these sections is documented below.

Dataset core metadata
'''''''''''''''''''''

The core :py:class:`~.Dataset` attributes are very generic and easily 
explained::

  "dataset": {
    "name": "machine-name",
    "label": "Nicer, human-friendly Title",
    "currency": "EUR",
    "description": "This can be Markdown-formatted"
  }

The ``name`` of the dataset will be part of each URL that refers to it, so it
makes sense to choose a concise term without any special characters, such
as spaces, symbols or text with accents or umlauts.

``currency`` is expected to be a valid, three-letter currency code, e.g. 
*EUR* or *USD*. All measures are by default assumed to be specified in 
this currency, unless otherwise noted.

Dimension and mapping definitions
'''''''''''''''''''''''''''''''''

The second section of the model, ``mapping``, serves a duplicate function: it 
is both used to define how the data should be modelled in OpenSpending and how
values for each attribute can be located within a source CSV file. Future 
versions of OpenSpending may break this up, defining both a ``model`` and 
``mapping``. 

The ``mapping`` section defines a set of fields to define the dataset model, each 
of which that can have one of four types (see :ref:`olap-intro` for a more 
detailed explanation):

 * ``measure`` to define a monetary attribute, such as the transaction amount. 
   In fact, if a field called ``amount`` exists, it will always be considered a 
   :py:class:`~.Measure` - this is needed to support older versions of the model 
   format. The datatype of measures is always assumed to be a decimal number.

 * ``value`` to define an :py:class:`~.AttributeDimension` attribute dimension, 
   such as a transaction ID. The datatype for value dimensions has to be set 
   explicitly but it will fall back to ``string``.

 * ``date`` to set a :py:class:`~.DateDimension`. Note that dates are always 
   assumed to be given in an ISO-style date format, such as *YYYY-MM-DD*, 
   *YYYY-MM* or *YYYY*. For compatibility reasons, any field with the name 
   ``time`` is assumed to be a ``date`` type dimension.

 * *any other type value* will be treated as a :py:class:`~CompoundDimension`. 
   For historic reasons, this is often set to ``classifier`` or ``entity``. 
   Note that, since compound dimensions have :py:class:`~Attribute` s, their 
   model syntax varies from that of the other types.

For dimensions of the types ``measure``, ``value`` and ``date``, a simple mapping
format is available::

  "mapping": {
    "amount": {
      "type": "measure",
      "label": "Amount paid",
      "description": "...",
      "column": "amt",
      "default_value": 0.0
    },
    "time": {
      "type": "date",
      "label": "Time of transaction",
      "description": "...",
      "column": "year_paid"
    },
    "transaction": {
      "type": "value",
      "label": "Transaction ID",
      "description": "12-digit identifier for each entry.",
      "column": "tx_id",
      "datatype": "string",
      "default_value": "<No ID>",
      "key": true
    }
  }

The mapping above defines three fields, one measure and two dimensions. The
meaning of ``type``, ``label`` and ``description`` are somewhat 
self-explanatory. ``column`` is used to define the source column where data
for this attribute can be found when the dataset is loaded form a CSV file.
If such a column cannot be found (or when it is empty), the system can fall
back to a ``default_value``, which will be used instead to fill up missing 
values. The ``default_value`` will not be used, however, if data is present 
but invalid (e.g. numeric columns with textual values, invalid dates). Such
errors will never be loaded and yield an error. The same is true of attributes
with empty values for which no ``default_value`` has been set (such as 
``time`` in the example above).

An important property is the ``key`` flag. This will include each flagged
dimension on the creation of a unique key for each entry. At least one
dimension must be flagged in this way, but the data contained must be 
sufficient to uniquely identify the record with the dataset - otherwise 
successive records with the same key set will overwrite previous ones. The 
mechanism is explained in more detail in :ref:`physical-model`.

The ``datatype`` property of the attribute dimension is used to convert the
found values into another format as needed. Valid types include: ``string``,
``id`` (will generate a slug-like string), ``float`` and ``date``.

Attributes (and attribute dimensions) of the ``date`` type support a further
option, ``format``. It can be used to specify a ``strptime``-compatible 
date parsing format to be used for the values in this column.

A valid input CSV file for the model defined above might look like this:

  ============= ============= ===========
  tx_id         year_paid     amt       
  ============= ============= ===========
  D38DEF-ZZ     2008          5044.0     
  AAA372-39     2011          43.5       
  (missing)     2009          2854922.0  
  ============= ============= ===========

In order to generate a :py:class:`~.CompoundDimension`, a somewhat more complex 
field description is required, as each of the sub-attributes must be defined 
independently.::

  "mapping": {
    "recipient": {
      "type": "entity",
      "label": "Recipient of Funds",
      "description": "Final destination of the transaction.",
      "facet": true,
      "attributes": {
        "name": {
          "column": "recipient_name",
          "datatype": "id",
          "default_value": "unknown"
        },
        "label": {
          "column": "recipient_name",
          "datatype": "string",
          "default_value": "Unknown Recpient"
        },
        "city": {
          "column": "recipient_city",
          "datatype": "string"
        }
      ]
    }
  }

As you will note, part of the properties of the :py:class:`~.Dimension` are 
still defined the same way (e.g. ``label``, ``description`` and the ``facet`` 
flag which tells the entry browser to include this dimension in the right-hand 
facet bar). All those properties which relate to the content of the data 
(where it comes from, how it is to be interpreted) must now be set for each 
:py:class:`~.Attribute` of the dimension individually: ``column``, ``datatype`` 
and ``default_value``. The key of the element in the ``attributes`` mapping
is used to specify a name for the attribute (see :ref:`name-conventions` for 
commonly used and expected attribute names).


Views and pre-defined visualizations
''''''''''''''''''''''''''''''''''''

A frontend feature of OpenSpending is the option to display pre-defined 
visualizations on the resource pages for datasets and dimensions. These 
views show the (total) amount of all entries matching the individual 
dataset or dimension member (e.g. ``/cra/cofog1/3`` - all UK healthcare
expenditure), broken down by some other dimension (e.g. ``region``, the 
geographic area in which the spending occurred). Such a breakdown can be
used to power tools such as tables and visualizations in the frontend.

As any dataset or dimension member may have several views associated with
it, each view has a ``name``. If the user does not explicitly select a 
view by its ``name``, the ``default`` view will be selected (the ``default``
view needs to be defined just like any other view, if it does not exist, 
the entries browser is shown instead).

As views can both be applied to a :py:class:`~.Dataset` and a 
:py:class:`~.Dimension`, two formats exist for their specification::

  "views": [
    {
      "name": "default",
      "label": "Spending by function",
      "entity": "dataset",
      "dimension": "dataset",
      "drilldown": "function"
    }
  ]

This view is applied to the :py:class:`~.Dataset` (i.e. it will be shown when 
the user visits the dataset home page) by specifying ``dataset`` as the 
``entity``. The view shows the total sum of the entries in the dataset divided 
into the different values of the dimension ``function``. Note that in this case, 
the ``dimension`` property does not carry a special meaning. The ``label`` will 
be shown in the user interface to allow the user to select amongst different 
views. ::

  "views": [
    {
      "name": "default",
      "label": "Spending by region",
      "entity": "dimension",
      "dimension": "function",
      "drilldown": "region",
      "cuts": {
        "spending_type": "local"
      }
  ]

This second view applies to all members of the :py:class:`~.Dimension` 
``function``, i.e. it will be shown whenever the user visits a dimension 
member page such as ``/dataset/function/health-services``. In this case, 
a more complex aggregation is performed: not only is the total amount of 
entries that match the dimension member value broken down by their ``region``, 
but we're also applying a filter on the dimension ``spending_type`` to 
only include those entries where this dimension has the specified value.

Special care needs to be taken in order for the ``name`` of each view not
to be ambiguous: the user must ensure that the value tuples of 
``(name, dimension)`` (or ``name``, ``dataset``) are only used once.


.. _physical-model: 

Physical model
--------------

When loading a :py:class:`~.Dataset`, OpenSpending will generate a set of 
tables (and columns) to represent the data. A table called 
``<dataset_name>__entry`` will be generated for each dataset with an ``id`` 
column. The ``id`` is generated from a defined set of attributes 
(those marked as *keys*) of each entry by hashing each value. The ID is 
therefore stable even is the data is re-loaded or the same record is 
inserted twice (i.e. an entry that has the same unique keys as one which is 
already loaded will overwrite the existing record).

On the facts table, a single numeric column will be generated for each 
:py:class:`~.Measure`. Other metadata (e.g. the currency of the measure) will 
not be stored on the fact table but kept in the dataset metadata.

:py:class:`~.AttributeDimension` are roughly equivalent to measures in technical 
terms, i.e. they also generate a single column on the fact table. The 
generated column will have the datatype specified in the model.

For :py:class:`~.CompoundDimension`, both a column on the fact table and a 
dedicated table will be generated. The table will have a name of the form 
``<dataset_name>__<dimension_name>``, with an auto-incrementing integer 
``id`` column. A column with a name of the form ``<dimension_name>_id`` 
is added to the facts table as a foreign key reference to the dimension 
table. For each :py:class:`~.Attribute` of the compound dimension, a column 
will be generated with the appropriate type. In order to identify the 
dimension, each member is assumed to have a ``name`` attribute. 
If no ``name`` is defined, the loader will attempt to auto-generate a value 
from an attribute called ``label``. If label also does not exist, the loader will
fail and require you to add a ``name`` attribute.

.. _name-conventions:

Attribute name conventions
''''''''''''''''''''''''''

OpenSpending also gives special importance to a set of other attributes of
compound dimensions so that it makes sense to define as many of them as 
possible:

* ``name`` must be a unique, identifying key for each member of the 
  dimension. 
* ``label`` is assumed to be a human-readable identifier that will be used 
  as a title and heading for the dimension member pahe and references to the
  member in general.
* ``uri`` contains a unified URI for the entity mentioned in this dimension, 
  e.g. an OpenCorporates URI or a reference to a classificiation scheme.
* ``color`` will be used when the dimension member is included in 
  visualizations. If no color is set, it will be selected from a pre-defined
  palette.
* ``parent`` is reserved for future use.

Querying the Model
------------------

There is a very limited number of different query types that are executed 
against the generated tables. 

For non-aggregated access, an :py:meth:`~.Dataset.entries` query is generated 
to yield a full view of the entries in a test dataset with all dimensions 
joined to the facts table, e.g.::

  SELECT function.id AS function_id, function.name AS function_name, 
         function.label AS function_label, entry.source AS entry_source, 
         "to".id AS to_id, "to".name AS to_name, "to".label AS to_label,
         entry.amount AS entry_amount
  FROM dataset__entry AS entry
    JOIN dataset__function AS function ON function.id = entry.function_id
    JOIN dataset__to AS "to" ON "to".id = entry.to_id
  WHERE 1=1

Alternatively, multiple entries can be aggregated using SQL's GROUP BY, SUM
and COUNT function. This is an :py:meth:`~.Dataset.aggregate` query that 
generates output to satify the simple cubes API used by most of visualizations 
running on OpenSpending::

  SELECT sum(entry.amount) AS amount, count(entry.id) AS entries,
         function.id AS function_id, function.name AS function_name,
         function.label AS function_label, entry.field AS entry_field,
         time.yearmonth AS time_yearmonth
  FROM dataset__entry AS entry
    JOIN dataset__function AS function ON function.id = entry.function_id
    JOIN dataset__time AS time ON time.id = entry.time_id
  GROUP BY function.id, time.yearmonth, entry.field
  ORDER BY amount desc

