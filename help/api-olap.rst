How does OpenSpending store data?
=================================

OpenSpending maintains a collection of **datasets**, each of which 
represents spending or budgetary data from a separate source that 
has its own data model. Inside each dataset, a set of **entries** are 
stored to represent individual transactions. 

Measures and Dimensions
'''''''''''''''''''''''

Each entry has several properties, such as the amount spent, a time 
stamp and several other dimensions to identify the data. 

There are different types of properties: **measures** are numeric units 
which contain the actual value of the entry (i.e. the monetary value of the 
transaction). They can be aggregated by some criterion, for example in 
order to sum up all transactions destined for a certain supplier. 

To contextualize these numeric values, **dimensions** contain other types 
of data that is available for the entry, e.g. a transaction number, 
classification scheme or involved company or individual. 

Dimensions can either hold a single value (so-called *Attribute Dimensions*) 
or a nested set of values (*Compound Dimensions*). Each compound dimension 
is identified through a name which makes it unique within the given dimension.

As a matter of convention, composite dimensions also have a human-readable 
label as well as a color used to represent it in visualizations. A special 
type of nested structures is used to represent dates in a way that lends 
itself to easy aggregation.


Slicing and Dicing the Data
'''''''''''''''''''''''''''

This storage structure is often referred to as a data cube, which represents
a multi-dimensional spreadsheet. When working with the cube, filters on 
dimensions are often used to select a relevant subset of the data. It is 
useful to think of these operations in terms of a cube from which you can 
**slice** (filter) certain segments while dividing the resulting part of the
cube by other criteria in a **drilldown** (dicing) operation.

On a technical level, all entries of a dataset are stored both in a set of 
auto-generated database tables and in a full text search index. Both 
mechanisms are sometimes used to produce aggregates, which may lead to
(floating-point imprecision based) differences between their results.


