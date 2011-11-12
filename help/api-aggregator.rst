Aggregation API
===============

The data source used to drive visualizations is the aggregation API. It 
can be used to flexibly generate aggregated views of the data by 
applying filters and grouping criteria.

This API is heavily based on OLAP concepts and the documentation assumes 
you have read :doc:`api-olap`. 

Basic call and parameters
'''''''''''''''''''''''''

.. code-block:: rest

  GET /api/2/aggregate?dataset=<dataset>

Calls will return aggregation results as JSON. If no arguments other than the 
dataset are given, the whole cube is aggregated. The following parameters are supported:

``dataset`` (required)
  The dataset name to query.

``measure``
  The name of the measure over which aggregation will be performed. Defaults to 
  ``amount``. Multiple measures in a single query are not yet supported, but future 
  versions of the API may aggregate over all available measures by default.

``cut``
  Filter the entries to use only a part of the cube. Only cells matching all the 
  criteria given will be used. With ``cut=time.year:2009``, you can filter for an
  attribute value. 
  
  Multiple filters can be given separated by a pipe character:
  ``cut=time.year:2009|category.name:health``. If two different filters are applied
  to the same attribute, the query will include both results: 
  ``cut=time.year:2009|time.year:2010`` The dimensions you use for cut will be part 
  of the returned result.

``drilldown``
  Dimension to be drilled down to. Each drilldown will split the result set to create
  a distinct result (cell) for each value of the dimension or attribute in 
  ``drilldown``. 
  
  For example ``drilldown=time.year`` will return all entries in the source data 
  broken down by year. Multiple drilldowns can be combined: ``drilldown=year|category`` 
  will return one cell for each year/category combination.

``page``
  Page number for paginated results, defaults to ``1``. 

``pagesize``
  Size of a page for paginated results, defaults to ``10000``.

``order``
  List of attributes to be ordered by as a combination of ``criterion:dir`` 
  pairs. The indicated direction is either ``asc`` for ascending order 
  or ``desc`` for descending order. For example ``order=year:asc|category:asc`` 
  sorts by year and then by category name.

The api itself is inspired by `DataBrewery Cubes <http://packages.python.org/cubes/server.html#api>`_, 
to which we aim to be compatible. At the moment we only implement the ``aggregate`` call of 
this API and do not support hierarchical dimensions queries in the same way.

Result format
'''''''''''''

The result will contain two keys, summary and drilldown. The ``summary``
represents an aggregation of whole cuboid specified in the cut. The 
amount given is the sum of all drilldowns.

The ``drilldown`` contains a cell for each value of each drilled-down 
dimension. Cells includes the values of any attributes or dimensions
which served as drilldown criteria, as well as the ``cut`` attributes.

.. code-block:: javascript

 {
   "drilldown": [
     {
       "volume": {
         "name": "section-i",
         "label": "PARLIAMENT"
       },
       "amount": 267770600.0,
       "num_entries": 46,
     },
     {
       "volume": {
         "color": "#FF8C00",
         "name": "section-ii",
         "label": "COUNCIL"
       },
       "amount": 705435934.0,
       "num_entries": 26,
     },
   ],
   "summary": {
     "amount": 973206534.0,
     "num_drilldowns": 2,
     "num_entries": 72
   }
 }


Example: Where Does My Money Go?
''''''''''''''''''''''''''''''''

To highlight the use of this API, lets look at the UK Country
Regional Analysis dataset. This is a high-level survey of the 
UK budget and the original `Where Does My Money Go? <http://wheredoesmymoneygo.org>`_ 
page was based on this data. 

The first call we'll make will aggregate the complete dataset 
and give us a total sum (`result <http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra>`_)::

  GET /api/2/aggregate?dataset=ukgov-finances-cra

This is not very useful, however, as it includes UK spending 
over several years. So lets refine our query to include only
2010 figures (`result <http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010>`_)::

  GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010

Much better. Now we may want to know how these funds are distributed
geographically, so lets drill down by the `NUTS <http://epp.eurostat.ec.europa.eu/portal/page/portal/nuts_nomenclature/introduction>`_ 
names of each region of the UK (`result <http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=region>`_)::

  GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=region

Given an SVG file with the right region names, this could easily be
used to drive a CSS-based choropleth map with a bit of JavaScript 
glue on the client side.

Another set of dimensions of the CRA dataset is the `Classification of 
Functions of Government (COFOG) <http://unstats.un.org/unsd/cr/registry/regcst.asp?Cl=4>`_ 
which classifies government activity by its functional purpose. Like
many taxonomies, COFOG has several levels which we have modelled as 
three dimensions, cofog1, cofog2 and cofog3.

In order to generate a `BubbleTree <http://vis4.net/blog/posts/tutorial-bubble-tree/>`_ 
diagram, we want to break down the full CRA dataset by each of these 
dimensions (`result <http://openspending.org/api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=cofog1|cofog2|cofog3>`_)::

  GET /api/2/aggregate?dataset=ukgov-finances-cra&cut=time.year:2010&drilldown=cofog1|cofog2|cofog3

(Warning: this generates quite a lot of data, you may want to paginate 
the results to view it in your browser.)

As you can see, the aggregator API can be used to flexibly query the 
data to generate views such as visualizations, maps or pivot tables.

  
