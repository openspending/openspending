How does OpenSpending store data?
=================================

OpenSpending maintains a collection of ``datasets``, each of which represents spending or budgetary data from 
a separate source that has its own data model. Inside each dataset, a set of entries are created
to store the individual transactions within a dataset. Each entry has several properties, such as the 
amount spent, a time stamp and several other dimensions to identify the data. 

In technical terms, there are multiple types of properties: measures are numeric units which contain 
the actual value of the entry (i.e. the value of the transaction). They can be aggregated by some 
criterion, for example in order to sum up all transactions destined for a certain supplier. 

To contextualize these numeric facts, dimensions contain other types of data that is available for 
the entry: a transaction number, classification scheme or involved company or individual. Dimensions 
can either hold a single value (so-called *Attribute Dimensions*) or a nested structure (*Compound 
Dimensions*). Each compound dimension is identified through a name and a taxonomy, to which it is a 
member. The taxonomy used to identify classification schemes, or to otherwise name the category of 
values that occur in a dimension. As a matter of convention, composite dimensions also have a 
human-readable label as well as a color used to represent it in visualizations. A special type of 
nested structures is used to represent dates in a way that lends itself to easy aggregation.

When working with the database, filters on dimensions are often used to select a relevant subset of the
data. This is often referred to as a data cube, and it is useful to think of these operations in terms
of a cube from which you can isolate (slice) certain segments, splitting the resulting segments by 
another criterion (drilldowns).

On a technical level, all values are stored both in a set of auto-generated database tables and in a 
full text search index. Both mechanisms are sometimes used to produce aggregates, which may lead to
(floating-point imprecision based) differences between their results.


