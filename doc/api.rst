================
OpenSpending API
================

Conventions
===========

Authentication
--------------

Some actions in OpenSpending require authentication, particularly those that write to the system or aim to access protected data (e.g. pre-publication datasets). For this purpose, each user is provided an API key. The key is displayed in the *settings* (go to the dashboard and click on *Change* next to the Information header). You can use it to perform authentication by adding the following into the HTTP headers (change <your-api-key> to the API key you find in your settings)::

    Authorization: ApiKey <your-api-key>

JSON-P Callbacks
----------------

All API calls that return JSON support JSON-P (JSON with padding). You can 
add a ``?callback=foo`` parameter to any query to wrap the output in a 
function call. This is used to include JSON data in other sites that do not
support CORS::

    $ curl http://openspending.org/cra.json?callback=foo

    foo({
        "description": "Data published by HM Treasury.", 
        "name": "cra", 
        "label": "Country Regional Analysis v2009", 
        "currency": "GBP"
    });

This can be used in remote web pages to include data as a simple ``script``
tag::

    <script>
      function foo(data) { 
        alert(data.label); 
      }
    </script>
    <script src="http://openspending.org/cra.json?callback=foo"></script>

Aggregate API
=============

The data source used to drive visualizations is the Aggregate API. It 
can be used to flexibly generate aggregated views of the data by 
applying filters and grouping criteria.

This API is heavily based on OLAP concepts, and the documentation assumes 
you know `how we store data`_.

.. _how we store data: http://community.openspending.org/help/guide/en/


Basic call and parameters
-------------------------

::

    GET /api/2/aggregate?dataset=<dataset>

Calls will return aggregation results as JSON. If no arguments other than the 
dataset are given, the whole cube is aggregated. The following parameters are supported:

* ``dataset`` (required)
  The dataset name to query.

* ``measure``
  The name of the measure over which aggregation will be performed. Defaults to 
  ``amount``. 

  Multiple measures in a single query are supported, separated by a pipe character:
  ``measure=amount|budget`` (sums up the amount measure *and* the budget measure).

* ``cut``
  Filter the entries to use only a part of the cube. Only cells matching all the 
  criteria given will be used. With ``cut=time.year:2009``, you can filter for an
  attribute value. 
  
  Multiple filters can be given separated by a pipe character:
  ``cut=time.year:2009|category.name:health``. If two different filters are applied
  to the same attribute, the query will include both results: 
  ``cut=time.year:2009|time.year:2010`` The dimensions you use for cut will be part 
  of the returned result.

* ``drilldown``
  Dimension to be drilled down to. Each drilldown will split the result set to create
  a distinct result (cell) for each value of the dimension or attribute in 
  ``drilldown``. 
  
  For example, ``drilldown=time.year`` will return all entries in the source data 
  broken down by year. Multiple drilldowns can be combined: ``drilldown=year|category`` 
  will return one cell for each year/category combination.

* ``page``
  Page number for paginated results. Defaults to ``1``. 

* ``pagesize``
  Size of a page for paginated results. Defaults to ``10000``.

* ``order``
  List of attributes to be ordered by as a combination of ``criterion:dir`` 
  pairs. The indicated direction is either ``asc`` for ascending order 
  or ``desc`` for descending order. For example, ``order=year:asc|category:asc`` 
  sorts by year and then by category name.

The API itself is inspired by `DataBrewery Cubes`_,
with which we aim to be compatible. At the moment, we only implement the ``aggregate`` call of 
this API and do not support hierarchical dimension queries in the same way.

.. _DataBrewery Cubes: http://packages.python.org/cubes/server.html#api

Result format
-------------

The result will contain two keys, ``summary`` and ``drilldown``. The ``summary``
represents an aggregation of the whole cuboid specified in the cut. The 
amount given is the sum of all drilldowns.

The ``drilldown`` contains a cell for each value of each drilled-down 
dimension. Cells include the values of any attributes or dimensions
which served as drilldown criteria, as well as the ``cut`` attributes.

::

    {
      "drilldown": [
        {
          "volume": {
            "name": "section-i",
            "label": "PARLIAMENT"
          },
          "amount": 267770600.0,
          "num_entries": 46
        },
        {
          "volume": {
            "color": "#FF8C00",
            "name": "section-ii",
            "label": "COUNCIL"
          },
          "amount": 705435934.0,
          "num_entries": 26
        },
      ],
      "summary": {
        "amount": 973206534.0,
        "num_drilldowns": 2,
        "num_entries": 72
      }
    }

JSON is the default format but results of the aggregation can also be downloaded as a csv file. Just add ``format=csv`` to the URL parameters to fetch them as a csv file.

Example: Where Does My Money Go?
--------------------------------

To highlight the use of this API, let's look at the UK Country
Regional Analysis dataset. This is a high-level survey of the 
UK budget, and the original `Where Does My Money Go?`_ page was based on this data. 

.. _Where Does My Money Go?: http://wheredoesmymoneygo.org

The first call we'll make will aggregate the complete dataset 
and give us a total sum (result: http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra)::

    GET /api/2/aggregate?dataset=ukgov-finances-cra

This is not very useful, however, as it includes UK spending 
over several years. So let's refine our query to include only
2010 figures (result: http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010)::

    GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010

Much better! Now we may want to know how these funds are distributed
geographically, so let's drill down by the [NUTS](http://epp.eurostat.ec.europa.eu/portal/page/portal/nuts_nomenclature/introduction)
names of each region of the UK (result: http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=region)::

    GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=region

Given an SVG file with the right region names, this could easily be
used to drive a CSS-based choropleth map, with a bit of JavaScript 
glue on the client side.

Another set of dimensions of the CRA dataset is the [Classification of 
Functions of Government (COFOG)](http://unstats.un.org/unsd/cr/registry/regcst.asp?Cl=4), 
which classifies government activity by its functional purpose. Like
many taxonomies, COFOG has several levels, which we have modelled as 
three dimensions: cofog1, cofog2 and cofog3.

In order to generate a Bubble Tree
diagram, we want to break down the full CRA dataset by each of these 
dimensions (result: http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=cofog1|cofog2|cofog3)::

    GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=cofog1|cofog2|cofog3

(Warning: this generates quite a lot of data. You may want to paginate 
the results to view it in your browser.)

As you can see, the aggregator API can be used to flexibly query the 
data to generate views such as visualizations, maps or pivot tables.

REST Resources
==============

OpenSpending pages generally support multiple representations, at least 
a user-facing HTML version and a JSON object that represents the contained
data. For various technical and non-technical reasons, most of the data is 
read-only.

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

The key resources in OpenSpending are datasets, entries, dimensions, and 
dimension members. Each of these has a listing and an entity view that can
be accessed.

Listing datasets
----------------

::

    GET /datasets.json

All datasets are listed, including their core metadata. Additionally, certain 
parameters are given as facets (i.e. territories and languages of the
datasets). Both ``territories`` and ``languages`` can also be passed in as 
query parameters to filter the result set. Supported formats are HTML, CSV and JSON.

::

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
        "description": "The Country Regional Analysis published by HM Treasury.",
        "currency": "GBP"
      },
      /* ... */
    ]

Getting dataset metadata
------------------------

::

    GET /{dataset}.json

Core dataset metadata is returned. This call does not have any 
parameters. Supported formats are HTML and JSON.

::

    {
      "name": "cra",
      "label": "Country Regional Analysis v2009",
      "description": "The Country Regional Analysis published by HM Treasury.",
      "currency": "GBP"
    }

Another call is available to get the full model description of 
the dataset in question, which includes the core metadata and also
a full description of all dimensions, measures, and views. The
format for this is always JSON::

    GET /{dataset}/model.json

Listing dataset dimensions
--------------------------

::

    GET /{dataset}/dimensions.json

A listing of dimensions, including type, description, and attribute
definitions is returned. This call does not have any parameters. 
Supported formats are HTML and JSON.

::

    [
      {
        "name": "from", 
        "html_url": "http://openspending.org/ukgov-finances-cra/from", 
        "label": "Paid from", 
        "key": "from", 
        "attributes": {
          "gov_department": {
            "column": null, 
            "facet": false, 
            "constant": "true", 
            "datatype": "constant", 
            "end_column": null
          }, 
          "name": {
            "column": "dept_code", 
            "facet": false, 
            "constant": null, 
            "datatype": "string", 
            "end_column": null
          }, 
          "label": {
            "column": "dept_name", 
            "facet": false, 
            "constant": null, 
            "datatype": "string", 
            "end_column": null
          }
        }, 
        "type": "compound", 
        "description": "The entity that the money was paid from"
      },
      /* ... */
    ]

Listing dimension members
-------------------------

::

    GET /{dataset}/{dimension}.json

The returned JSON representation contains the dimension metadata, 
including type, label, description and attribute definitions. 

::

    {
      "name": "from", 
      "html_url": "http://openspending.org/ukgov-finances-cra/from", 
      "label": "Paid from", 
      "key": "from", 
      "attributes": {
        "gov_department": {
          "column": null, 
          "facet": false, 
          "constant": "true", 
          "datatype": "constant", 
          "end_column": null
        }, 
        "name": {
          "column": "dept_code", 
          "facet": false, 
          "constant": null, 
          "datatype": "string", 
          "end_column": null
        }, 
        "label": {
          "column": "dept_name", 
          "facet": false, 
          "constant": null, 
          "datatype": "string", 
          "end_column": null
        }
      }, 
      "type": "compound", 
      "description": "The entity that the money was paid from"
    }

This call's return includes dimension metadata, but it may be too expensive
to call for just this aspect.

Getting dimension members
-------------------------

::

    GET /{dataset}/{dimension}/{name}.json

This will return the data stored on a given member ``name`` of the 
``dimension``, including its ``name``, ``label``, and any other
defined attributes. 

::

    {
      "id": 2, 
      "name": "10",
      "label": "Social protection", 
      "description": "Government outlays on social protection ...",
      "level": "1"
    }

Listing entries in a dataset
----------------------------

Listing all the entries in a dataset (and offering export functionality)
is handled by the full-text search. See [the search API](../search).

Getting an entry
----------------

::

    GET /{dataset}/entries/{id}.json

This will return a full representation of this entry, including all 
measures and all attributes of all dimensions. The entry ``id`` is a 
semi-natural key derived from dataset metadata which should be stable 
across several loads.

A CSV representation is available but will only have one row.

Full-text Search API
====================

OpenSpending supports full-text search as a research tool for 
everyone who wants to investigate the spending information kept
in our database.

It is important to note, however, that search is always performed
on individual entries. More abstract concepts (e.g. "all 
health spending in a country over a given year") would mostly be the
result of adding up many individual entries. If your use case
requires that you access such concepts, you may want to look at
the [aggregation API](../aggregation) instead.

Basic call and parameters
-------------------------

::

    GET /api/2/search?q=<query>

Calls will return a set of fully JSON serialized entries, query
statistics, and, depending on the other parameters, other data such as 
facets.

The following parameters are recognized:

* ``q``
  Query string. Will usually search a composite text field but can 
  be limited to a specific field (i.e. a dimension, attribute, or measure)
  with ``field:value``. Boolean operators such as OR, AND, and ±term can also be used.

* ``dataset``
  Specifies a dataset name to search in. While searching across multiple
  datasets is supported, this parameter can be used to limit the scope and
  increase performance. It can be used multiple times or multiple
  dataset names can be separated with pipe symbols.

* ``category`` 
  The dataset category can be used to filter datasets by their type,
  e.g. limiting the output to only transactional expenditure (and
  excluding any budget items). Valid values include ``budget``, 
  ``spending``, and ``other``.

* ``stats``
  Includes solr statistics on measures, namely the average, mean, and
  standard deviations. This is generated through the indexed data and 
  can differ marginally from the 
  results of the aggregator due to floating point inaccuracies.
  Note that aggregations
  across datasets with different currencies (or even the same currency
  across different years) are possible but must be avoided.

* ``filter``
  Apply a simple filter of the format ``field:value``. Multiple filters
  can be joined through pipes, e.g. ``fieldA:value|fieldB:value``.

* ``page``
  Page number for paginated results. Defaults to ``1``. 

* ``pagesize``
  Size of a page for paginated results. Defaults to ``10000``.

* ``facet_field``
  A field to facet the search by, i.e. give all the distinct values of
  the field in the result set with the count of how often each occurred.

* ``facet_page``, ``facet_pagesize`` 
  Works analogously to the ``page`` and ``pagesize`` parameters but applies
  to facets instead.

* ``expand_facet_dimensions``
  When a compound dimension name is used for a facet, this will return a 
  full representation of this dimension value for each value. 
 
If an error is detected, the system will return a simple JSON response
with a list of ``errors`` describing the fault. 

Solr query syntax
-----------------

OpenSpending uses Apache Solr for full-text indexing. Some search
parameters are passed directly to Solr::

    GET /api/2/search?q=money%20measure:[min%20TO%20max]&fq=dimension:value

Some useful resources to explore the query language of Solr include:

* Solr Common Query Parameters: http://wiki.apache.org/solr/CommonQueryParameters
* Lucene Query Parser Syntax: http://lucene.apache.org/java/3_4_0/queryparsersyntax.html
* Solr Query Syntax: http://wiki.apache.org/solr/SolrQuerySyntax (Advanced)

Personal Tax API
================

The tax share API estimates a household's tax contribution based on simple 
proxy data. The estimate allows for both direct tax (including income tax, 
national insurance and council tax) and indirect tax (including VAT, alcohol 
and tobacco duty, and fuel duty).

::

    GET http://openspending.org/api/mytax?income=N

The basic call accepts a variety of parameters, most of which are optional:

* ``income`` (required)
  Total household income, including all pension and benefits. This is 
  used to estimate total tax paid, including both direct and indirect 
  taxation.

* ``spending`` 
  Total spending on consumption.

* ``smoker``
  yes/no

* ``drinker``
  yes/no

* ``driver``
  yes/no

This will generate a simple JSON response of the following form::

    {
      "alcohol_tax": 153.04239230064161,
      "explanation": [
        "This household income falls between national average income decile 1 (which has average gross household income of 9219.00, and pays 1172.00 in direct tax, 1016.00 in VAT, 1101.00 in smoking taxes, 288.00 in alcohol-related taxes, 150.00 in car-related taxes, and 349.00 in other indirect taxes), and decile 2 (which has average gross household income of 13583.00, and pays 1368.00 in direct tax, 969.00 in VAT, 1085.00 in smoking taxes, 310.00 in alcohol-related taxes, 167.00 in car-related taxes, and 289.00 in other indirect taxes).",
        "Therefore, a household with an income of 10000.00 pays approximately 1207.08 in direct tax and 2888.97 in total indirect tax."
      ],
      "tax": 4096.0439963336394,
      "tobacco_tax": 291.93721356553618,
      "car_related_tax": 338.26214482126488,
      "total_direct_tax": 1207.076993583868,
      "vat": 1098.1365719523374,
      "total_indirect_tax": 2888.9670027497709
    }  

Permissions API
===============

OpenSpending allows users to check for their permissions on a given dataset via an API call. The response will provide the authenticated user's permission on as true or false values for *CRUD* (create, read, update, and delete). This API call mainly exists to allow software that uses the API (e.g. the loading API) to save bandwidth with big dataset updates.

For example if you as a developer are building a loading script that users of OpenSpending can use to download data from a location and update datasets in OpenSpending you might first run a check for permissions based on their API key before starting to download the updates (so you can skip it if they're not authorized).

The permission API works as follows. Make a *GET* request (wih user authenticated with the API key) to::

    /api/2/permissions?dataset=[dataset_name]

The response will be single json object with four properties, *create*, *read*, *update*, and *delete*. The value of each property is a boolean (true or false) that indicates if the authenticated user has that permission for the provided dataset::

    {
        "create": false,
        "read": true,
        "update": false,
        "delete": false
    }

Loading API
===========

Users can load datasets (or add sources to them) by making a *POST* request to ``https://openspending.org/api/2/new`` (notice *https*) with the following url parameters:

* *csv_file* - A **url** to the csv file to me imported for the dataset
* *metadata* - A **url** to the json file with dataset metadata (name, currency, etc.) and the model. Views can also be defined in this file. Take a look at a sample json file - https://dl.dropbox.com/u/3250791/sample-openspending-model.json to see how it should be structured (the value for *mapping* is the model - how the csv file should be cast into dataset dimensions, and the value for *dataset* is the metadata itself). To gain a better understanding of how to do the mapping, take a look at the corresponding csv file - http://mk.ucant.org/info/data/sample-openspending-dataset.csv.
* *private* - A **boolean** ("true"/"false") indicating whether the loaded dataset should be private or not (made public). By default new datasets loaded via the API are made public. If an existing dataset is updated via the loading API the *private* parameter does nothing and the private setting is retained.

Along with these parameters an api key must be provided in the header of the request. For more details see [API Conventions](/help/api/conventions/).

Budget Data Packages
--------------------

Generating the *metadata* file can be complex. If you have prepared a `budget data package`_ for your data, that can also be loaded into OpenSpending via the same API endpoint (i.e. the Loading API endpoint). Instead of providing *csv_file* and *metadata* url parameters, you use a different parameter:

* *budget_data_package* - A **url** to you budget data package descriptor file, e.g. https://budget.example.com/my-budget-data-package/datapackage.json

The *private* boolean parameter still works in the same way as before.

.. _budget data package: https://github.com/openspending/budget-data-package/blob/master/specification.md
