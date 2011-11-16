
Search API
==========

OpenSpending supports full-text search as a research tool for 
everyone who wants to investigate the spending information kept
in our database.

It is important to note, however, that search is always performed
on individual entries. More abstract concepts, such as "All 
health spending in a country over a given year" may only be 
represented as the result of adding up many individual entries. 

If your use case requires that you access such concepts, you may 
want to look at the :doc:`api-aggregator` instead.

.. _entry-browsers:

Entry Browsers and Bulk Export
''''''''''''''''''''''''''''''

Entries pages both for the whole dataset and specific dimensions 
are powered by a shared search interface that can be queried 
programmatically. 

Examples for such search entry points include:

* ``/<dataset>/entries`` - Search all the entries in a given dataset.
* ``/<dataset>/<dimension>/<member>/entries`` - Search all entries 
  where a given ``dimension`` has a specific value ``member``.

The following parameters are recognized:

``q``
  Query string, will usually search a composite text field but can 
  be limited to a specific field (i.e. a dimension, attribute or measure)
  with ``field:value``. Boolean operators such as OR, AND and +term, 
  -term can also be used.

``page``
  Search result page, offset via ``limit``. Defaults to ``1``.

``limit``
  The maximal number of results to be returned. This defaults to ``50`` 
  for the HTML representation but does not apply by default to JSON and 
  CSV output (i.e. the whole result set is returned).

``filter-{field}``
  Filter the result set by the given value of the given ``field``.
 
The returned values can be CSV or JSON, depending on which file 
suffix is attached to the query path. The returned data is a 
serialization of the internal database format. By default, CSV and 
JSON representations do not apply a pagination limit and will thus 
trigger a **bulk export** unless otherwise specified.

The result data for JSON will also contain facets as specified in 
the dataset metadata description:

.. code-block:: javascript
  
  {
    "stats": {}, 
    "facets": {
      "cofog1.label_facet": {
        "Social protection": 11, 
        "Public order and safety": 5, 
        "Economic affairs": 12, 
        "Housing and community amenities": 8
      }, 
      "region": {
        "ENGLAND_South West": 20, 
        "SCOTLAND": 3, 
        "ENGLAND_Yorkshire and The Humber": 3, 
        "ENGLAND_West Midlands": 4, 
        "ENGLAND_London": 6
      }
    }, 
    "results": [
      /* list of full materialized entries. */
    ]
  }


Raw Lucene Queries
''''''''''''''''''

OpenSpending uses Apache Solr for full-text indexing and direct 
access to the search index is provided for advanced users. Search 
parameters are passed directly to Solr except for some checks and 
minor modifications (e.g. to ensure JSON is returned)::

  GET /api/search?q=money

You can generally use any parameters supported by Solr::

  GET /api/search?q=money%20measure:[min%20TO%20max]&fq=dimension:value

Unlike the browser API, the returned data for direct search will 
be in a flattened output format specific to the Solr index. Some 
useful resources include:

* `Solr Common Query Paramters <http://wiki.apache.org/solr/CommonQueryParameters>`_
* `Lucene Query Parser Syntax <http://lucene.apache.org/java/3_4_0/queryparsersyntax.html>`_
* `Solr Query Syntax <http://wiki.apache.org/solr/SolrQuerySyntax>`_ (Advanced)
* `Solr JSON Response Format <http://wiki.apache.org/solr/SolJSON#JSON_Query_Response_Format>`_




