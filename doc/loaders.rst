Loaders to import datasets into Open Spending
=============================================

.. currentmodule:: wdmmg.lib.loader

What are loaders
----------------

A loader is a way to import a :term:`dataset` into Open Spending.
These loaders use one or more :term:`dataset sources` and
create :term:`Entry`, :term:`Entity` and :term:`Classifier` entries
in the :term:`database`. You can use whatever python can read,for example *csv*,
*json*, *xls* or *xml* files. We also provide helper functions to read
data directly from google docs.

Note that we are working on a way to let users import *csv* files
with through the Open Spending web interface. 

.. fixme: update status for csv importer


How to write a loader
---------------------

In this section you will write a *demo loader* to import a simple csv
file that provides all the data we need. The minimal set of data you
need for an import spendings is (named with their internal keys):

``to``
    The recipient, which an :term:`Entity` (i.e. a source or sink for money). 
``from``
    The spender, also an :term:`Entity` .
``amount``
    The amount spent
``time``
    The time period to which the spending data refers. This could be years,
    month or days (but we usually analyze data per year. )
    
``currency``
    The currency the amount is quoted in.
``classifiers (optional)``
    Information to classify a spending :term:`Entry`, e.g. the region
    department or sector it was spent on. This is not required but
    can be used to provide the user different ways to explore the data.

Not all of this information has to be present in your data source. A
common case is that for all spending data ``to`` or ``from `` is the
society, or ``currency`` is alway the same, so you can hardcode values
in your data loader.

The :download:`demo source file <../wdmmg/tests/demoloader.csv>` is a csv
file that contains one spending :term:`Entry` per line. You know that the
``currency`` of all spendings is *EUR*. The file contains the
following columns:

``id``
    A distinct id for every spending :term:`Entry` (a journal number/number 
    of entry)
``spender_id``
    A distinct id for the spender.
``spender_name``
    The name of the spender.
``recipient_id``
    A distinct id for the recipient.
``recipient_name``
    The name of the recipient.
``region``
    The region the money is spent on.
``sector``
    The sector the money is spent on.
``date``
    The day the money is spent on.
``amount``
    The amount spent.

Here is your data (:download:`download demoloader.csv<../wdmmg/tests/demoloader.csv>`):

.. csv-table:: demoloader.csv
   :header: "id","spender_id","spender_name","recipient_id","recipient_name","region","sector","date","amount"
   
   "id","spender_id","spender_name","recipient_id","recipient_name","region","sector","date","amount"
   "demo-sp-001","dfes","Department for Education","dtlr","Department for the Regions","North Yorkshire","Social Protection","2010-01-01",1200000
   "demo-sp-002","dfes","Department for Education","dtlr","Department for the Regions","North Yorkshire","Education","2010-02-01",800000
   "demo-sp-003","dfes","Department for Education","society","General Public","North Yorkshire","Education","2011-03-01",500000
   "demo-sp-004","dtlr","Department for the Regions","society","General Public","Hartlepool","Health","2011-04-01",1400000
   "demo-sp-005","dtlr","Department for the Regions","dfes","Department for Education","Hartlepool","Heath","2010-05-01",260000
   "demo-sp-006","dtlr","Department for the Regions","dfes","Department for Education","Hartlepool","Social Protection","2011-06-01",1150000


Create a Loader
'''''''''''''''

.. testsetup:: demoloader
   
   from wdmmg.tests.demo import *

First you create a :class:`Loader`. This is a class that lets you
create :term:`Entry`, :term:`Entity` and :term:`Classifier` objects in
an Open Spending site easily, quickly and reliably without a deep
knowledge of the saved data structures.

.. literalinclude:: ../wdmmg/tests/demoloader.py
   :pyobject: make_loader
   :linenos: 

* *Line 2-5*: We create the loader

  * ``dataset_name``: is the (internal) name of our dataset. This should be
    unique within the database.
  * ``unique_keys``: the key (or combination of keys) that can identify
    one spending :term:`Entry` uniquely. In this case it is enough to use the content of
    the id column. You will use that as the ``name`` of an entry. Do
    not use ``id`` on any *Dataset*, *Entry*, *Entity* or *Classifier*
    **ever**. ``id`` has a special meaning internally.
  * ``label`` The dataset label that you present to the user on the website.
  * ``description``: A description you can present to the user. It's not
    strictly required but we recommend to add 1-2 sentences.
    
At the end you return the instanciated ``loader`` to use it later.
Internally the loader automatically creates a :class:`wdmmg.model.Dataset`
for you.

.. doctest:: demoloader
  
  >>> loader = make_loader
  >>> loader.dataset.name
  u'demodata'

See the :class:`Loader` API for the available methods and
the options to create it.


Read the data file
''''''''''''''''''

Now you can read the csv file. To do that, create a function that you
can pass the filename to (i.e. You don't need to write a second
function to read a second, similar file, can use the same function
multiple times). This is especially useful if you want to write tests
for your data loader.

.. literalinclude:: ../wdmmg/tests/demoloader.py
   :pyobject: read_data
   :linenos: 

* *Line 6*: Open the file
* *Line 7*: Use it to create a :class:`csv.DictReader`. It will
  create a list with a ``dict`` for every line in the file. The first
  line, the headers, will be used as keys in the ``dict``. See the python
  documentation for details how it works.
* *Lines 8-14*: Convert all values from the csv file to ``unicode`` values.
  Otherwise you may run into encoding errors later if the file contains
  non-ascii characters like french accent or german umlauts.
* *Line 16*: Return the ``rows``

.. note::
   If you want to work with massive amounts of data, you want
   to use generator functions in many places and ``yield`` the single
   rows for performance reasons.
 
Now you have a list with one dict for every row:

   >>> filename = '../wdmmg/tests/demoloader.csv'
   >>> rows = read_data(filename)
   >>> first_row = rows.next()
   >>> first_row
   {'amount': '1200000',
    'date': '2010-01-01',
    'id': 'demo-sp-001',
    'recipient_id': 'dtlr',
    'recipient_name': 'Department for the Regions',
    'region': 'North Yorkshire',
    'sector': 'Social Protection',
    'spender_id': 'dfes',
    'spender_name': 'Department for Education'}


Save the Entries into the database
''''''''''''''''''''''''''''''''''

Now that you have the dictionaries with the data you can save
it into the database. You have to refine the data a bit as
the DictReader returns dicts where the keys are the column headers,
and all values are strings. But:

1. The column ``id`` in the table will be the ``name`` of
   the *entry* you create.
2. The ``amount`` is a number.
3. ``date`` is a date. The main date of an *Entry* (the :term:`time
   axis` of the *dataset*) is treated specially. It is saved on the
   *Entry* with the key ``time`` and in a special data structure.
4. ``spender`` and ``recipient`` are not only text. In the *dataset*
   they are *Entities*. A :term:`Entity` is a person or a thing
   (e.g. an administrative region, a company etc) that can spend or
   receive money. *Entities* are not bound to a special *dataset*.
   E.g. one *entity* that we want to be unique across all datasets
   is the *society* (see :ref:`Default Society <defaultsociety>`) 
5. ``region`` and ``sector`` are not only text. They can be used to
   *classify* each entry. Users will be able to navigate 
   the data with the help of classifiers. A :term:`Classifier` is not bound
   to a dataset, it is part of a :term:`taxonomy`. E.g. the European
   Union has a system to classify spending entries of their Organisations
   and members (COFOG). Usually you reuse an existing *taxonomy* or create
   *one* custom to your *dataset*, but you could even create
   *Classifiers* in different *taxonomies*. 
   
Here we show you how to create custom ones.

So let's prepare the data and save *Entry*, *Entities* and *Classifiers*.

.. literalinclude:: ../wdmmg/tests/demoloader.py
   :pyobject: save_entry
   :linenos:

* *Line 19*: Save the time in a special datastructure.
  :mod:`wdmmg.lib.times` contains helper functions to create it.
* *Line 26, 31*: :meth:`Loader.create_entity` creates a
  :class:`wdmmg.model.Entity` object and saves it to the
  database automatically. If a *entity* with the same name exists
  already it will be updated.  The *entity* object is returned so you
  can use it.
* *Line 36, 38*: :meth:`Loader.create_classifier` creates a
  :class:`wdmmg.model.Classifier` object and saves it to the
  database automatically. If a *classifier* with the same *name*
  exists already in the same *taxonomy*, it will be updated. The
  *entity* object is returned so you can use it.
* *Line 42, 43*: Use the *classifiers* to classify the
  *entry_data*. Additional information will be added to the
  dict. *name* to become the key of the classifier. This can be used to
  get more information about the meaning of the classifier.
* *Line 46*: Finally create the :class:`wdmmg.model.Entry`.  It
  will be saved automatically in the database but *create_entry* will
  not return an *Entry* object for performance reasons.  It will
  return *query_spec* (a :term:`mongodb query spec`). If you have to do
  further work on the *entry* you can retrieve it with
  ``model.Entity.find_one(query_spec)``.


Describe the data for the users
'''''''''''''''''''''''''''''''

Sweet. The system can read your data and you can make a loader and
save entries and other data. So you're nearly there.

Most of the data you save is pretty standard. *Amount*, *sender*,
*recipient*, *currency* and *date* are generally understandable and
used across all datasets. But for special data (e.g. in the demo
dataset, *region* and *sector*), you need to describe how users should
interpret the data.

To describe the kind of data you store in the Entries use
Loader.create_dimension().


.. literalinclude:: ../wdmmg/tests/demoloader.py
   :pyobject: describe_keys
   :linenos:

Dimensions - Create views on the data
'''''''''''''''''''''''''''''''''''''

An Open Spending site does allow the user to explore the data with
Dimensions. To add a :term:`Dimension` use :meth:`Loader.create_view`.

.. note::

   fixme: this Section has to be written.


Put it all together
'''''''''''''''''''

To wire it all together, write a *load* function that finds the source
file and does all the things above. It's important to call 
:meth:`Loader.compute_aggregates` at the end. This will collect additional
information in the database.

.. literalinclude:: ../wdmmg/tests/demoloader.py
   :pyobject: load
   :linenos:

The complete loader can be :download:`downloaded here<../wdmmg/tests/demoloader.py>`.

Loaders are normally used on the command line with the command::

  paster load <loader_name>

To add your loader to the load command, add an entry point to the python
package you created in the *setup.py* for ``wdmmg.load``. In this case
the demo loader is located in wdmmg/tests/demoloader.py and the function
is ``load``:

.. code-block:: python

  setup(...
        entry_points="""
        [wdmmg.load]
        demo = wdmmg.tests.demoloader:load
        """
        )


Tests
-----

If you write a loader that is used by other people you should also write
tests to make sure everything works as expected. There might be changes
in newer versions of the source file or in newer versions of OpenSpending
that will be unnoted if there are no tests.

.. note:
   fixme: The tests are incomplete and should be extended.

You can find a set of tests in
:download:`test_demoloader.py <../wdmmg/tests/test_demoloader.py>`

.. literalinclude:: ../wdmmg/tests/test_demoloader.py


Tips and Tricks
---------------

.. _defaultsociety:

Default Society
'''''''''''''''
Often you have *entities* that name the *Society* as the spender or
recipient. You should not use ``create_entity()`` then but use
:meth:`Loader.get_default_society`.


Unique Keys/Names
'''''''''''''''''

The names for *Entries* must be unique for the dataset, the name of
*Classifiers* unique across all classifiers in the *taxonomy* and the
name of *Entities* unique within an OpenSpending installation.

This will most of the time be no problem. You often have unique id's
like journal numbers for the *Entries*. If you do not have them, you
can

* use functions from :mod:`wdmmgext.load.utils` to create keys
* prefix keys you have with the name of your dataset
* For *Classifiers* create a new taxonomy specific for your dataset. 

Hierarchies
'''''''''''
If you have a hierarchy, say:

* Department: "Department Foo"

  * Subdepartment: "Subdepartment Bar"

    * Bureau "Bureau for extraordinary affairs"

.. code-block:: python
   :linenos:

   foo = loader.create_entity('foo', "Department Foo")
   bar = loader.create_entity('bar', "Subdepartment Bar")
   bureau = loader.create_entity('extraordinary-affairs', "Bureau for ...")
   
   # now we have to add cross references:
   foo['subdepartment'] = bar
   foo.save()

   bar['department'] = foo
   bar['bureau'] = bureau
   bar.save()
   
   bureau['subdepartment'] = bar
   bureau.save()


*Line 7, 11, 14*: When you change an *Entity*, *Entry* or *Classifier* after
you have created it, you need to save them explicitly.

Alternatively you can only use 'parent' and 'child' as keys (instead
of 'department', 'subdepartment' and 'bureau').
