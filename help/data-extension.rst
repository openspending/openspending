How can I extend my data?
=========================

In order for your dataset to be more easily accessible to users, it often makes sense to add in 
additional data from other sources. For example, in a dataset of European tender award notices the 
CPV (common procurement vocabulary) code for each contract may be given. While the code itself is 
not very helpful, adding in the EU's descriptions of each code will give visitors of your dataset a 
clearer idea of what the money is being spent on.


Common merging criteria
'''''''''''''''''''''''

Here are some ideas for extending your data:

* **Classification codes** (such as the CPV mentioned above, COFOG, the classification of functions of 
  government, or DAC codes in development cooperation) often occur without much explanation in the source
  data. Try to find a code sheet that assigns names and hierarchies to these codes, so that users can
  understand what they mean and how they relate to each other. Sometimes classification schemes are 
  maintained only within an organization, so it may be worthwhile sending a freedom of information 
  request to get access to code sheets.

* **Companies and other organizations** are often identified only by their name and possibly their VAT code. Companies databases 
  such as OpenCorporates.com offer more information on each company that you can merge into your 
  dataset. Such information may include its geographic location, industry classifiers or board 
  members.

* Sometimes, separate databases are kept on project **finance and results reporting**. You might be looking at
  a dataset that only contains grant amounts and general information, when data on disbursement, 
  progress or more descriptive texts are available elsewhere. Try to find a linking element between 
  the two databases (e.g. a project ID) and to merge the two databases.

* **Geographic information** can be extended using various web services, such as OpenStreetMap. Using such
  services you may be able to infer state and country names from a given city label or even to include 
  geo-coordinates for projects.


Tool options for merging datasets
'''''''''''''''''''''''''''''''''

Some of these proposals require you to merge two or more spreadsheets. While this can be done in 
newer versions of Microsoft Excel and LibreOffice, data wrangling tools such as Google Refine (and its 
sadly underdocumented cell.cross() function) and Google Fusion Tables can be very useful in this 
regard. Depending on the amount of processing that you need to do, it may also make sense to import 
your data into a relational database such as SQLite. While there are visual frontends for these 
databases, using them to merge datasets will ususally require you to be familiar with SQL.


