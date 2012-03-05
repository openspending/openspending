
REST resources
==============

OpenSpending pages generally support multiple representations, at least 
a user-facing HTML version and a JSON object that represents the contained
data. For various technical and non-technical reasons, most of the data is 
read-only (see :doc:`api-loading`).

Content negotiation can be performed either via HTTP ``Accept`` headers or 
via suffixes in the resource URL. The following types are generally 
recognized:

* **HTML** (Hyptertext Markup), MIME type ``text/html`` or any value not 
  otherwise in use, suffix ``.html``. This is the default representation.
* **JSON** (JavaScript Object Notation), MIME type ``application/json`` and
  suffix ``.json``.
* **CSV** (Comma-Separated Values), MIME type ``text/csv`` and suffix 
  ``.csv``. CSV is only supported where listings can be exported with some
  application-level meaning.

The key resources in OpenSpending are datasets, entries, dimensions and 
dimension members. Each of these has a listing and an entity view that can
be accessed.

Listing datasets
''''''''''''''''

.. code-block:: rest

  GET /datasets.json

All datasets are listed, including their core metadata. Additionally, certain 
parameters are given as facets (i.e. territories and languages of the
datasets). Both ``territories`` and ``languages`` can also be passed in as 
query parameters to filter the result set. Supported formats are HTML, CSV and JSON.

.. code-block:: javascript

  
  "territories": [
    /* ... */
    {
      "count": 2,
      "url": "/datasets?territories=BH",
      "code": "BH",
      "label": "Bahrain"
    },
    /* ... */
  ],
  "languages": /* Like territories. */
  "datasets": [
    {
      "name": "cra",
      "label": "Country Regional Analysis v2009",
      "description": "The Country Regional Analysis published by HM Treasury (2010 version).",
      "currency": "GBP"
    },
    /* ... */
  ]


Getting dataset metadata
''''''''''''''''''''''''

.. code-block:: rest

  GET /{dataset}.json

Core dataset metadata is returned. This call does not have any 
parameters. Supported formats are HTML and JSON.

.. code-block:: javascript

  {
    "name": "cra",
    "label": "Country Regional Analysis v2009",
    "description": "The Country Regional Analysis published by HM Treasury (2010 version).",
    "currency": "GBP"
  }

Another call is available to get the full model description of 
the dataset in question, which includes the core metadata but also
a full description of all dimensions, measures and views. The
format for this is always JSON::

  GET /{dataset}/model.json

Listing dataset dimensions
''''''''''''''''''''''''''

.. code-block:: rest

  GET /{dataset}/dimensions.json

A listing of dimensions, including type, description and attribute
definitions is returned. This call does not have any parameters. 
Supported formats are HTML and JSON.

.. code-block:: javascript

  [
    {
      "description": "Central government, local government or public corporation", 
      "column": "cap_or_cur", 
      "label": "CG, LG or PC", 
      "datatype": "string", 
      "key": "cap_or_cur", 
      "type": "value"
    },
    /* ... */
  ]

Listing dimension members
'''''''''''''''''''''''''

This call also includes dimension metadata but may be too expensive
to call for just this aspect.

.. code-block:: rest

  GET /{dataset}/{dimension}.json

The returned JSON representation is a dictionary of two keys, ``meta``
and ``values``. ``meta`` keeps the dimension metadata, including type, 
label, description and attribute definitions. 

``values`` is a descending list of tuples, where the first element is 
a specific member (value) of the dimension and the second value is the 
total ``amount`` of all entries which have this value set for the 
dimension. A limit of 100 members is returned, but more can be retrieved 
using the ``page`` query parameter.

.. code-block:: javascript

  {
    "meta": {
      "key": "cofog1", 
      "label": "COFOG level 1"
      "description": "Classification Of Functions, level 1", 
      "fields": [
        {
          "column": "cofog1.name", 
          "datatype": "string", 
          "name": "name"
        }, 
        {
          "column": "cofog1.label", 
          "datatype": "string", 
          "name": "label"
        }, 
        /* ... */
      ], 
      "type": "compound", 
    }, 
    "values": [
      [
        {
          "description": "Government outlays on social ... ",
          "level": "1", 
          "taxonomy": "cofog", 
          "label": "Social protection", 
          "change_date": "", 
          "id": 2, 
          "name": "10"
        }, 
        191500000.0
      ],
      /* .... */
    ]
  }


Getting dimension members
'''''''''''''''''''''''''

.. code-block:: rest

  GET /{dataset}/{dimension}/{name}.json

This will return the data stored on a given member ``name`` of the 
``dimension``, including its ``name``, ``label`` and any other
defined attributes. 

.. code-block:: javascript

  {
    "id": 2, 
    "name": "10",
    "label": "Social protection", 
    "description": "Government outlays on social protection ...",
    "level": "1"
  }


Listing entries in a dataset
''''''''''''''''''''''''''''

Listing all the entries in a dataset (and offering export functionality)
is handled by the full-text search, please see :ref:`entry-browsers`.


Getting an entry
''''''''''''''''

.. code-block:: rest

  GET /{dataset}/entries/{id}.json

This will return a full representation of this entry, including all 
measures and all attributes of all dimensions. The entry ``id`` is a 
semi-natural key derived from dataset metadata which should be stable 
across several loads.

A CSV representation is available but will only have one row.
