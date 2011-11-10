Conceptual Overview
===================

OpenSpending is an open data project aimed at tracking public finance all 
over the world. The software is capable of loading and presenting many 
different types of data, including budgetary and spending data. In technical
terms, OpenSpending is an OLAP-inspired multi-tenant datamart that offers 
web interfaces to generate data models, trigger data imports, run searches, 
aggregation queries and REST-style requests against individual resources.


Rationale
'''''''''

The design of OpenSpending is based on the assumption of a three-stage
process that underlies most government finance transparency projects, 
independently of whether they are managed by transparency NGOs, civic 
hackers or journalists:

* **Data extraction and transformation.** Most projects need to extract
  data from a remote source; either through databases released in a 
  structured, machine-processable form or from sources with a lower 
  quality, such as unstructured web pages, PDF documents or paper-based 
  releases. In any case, the data needs to be brought into a common format
  and transformed to allow loading into a database. This includes assessing
  and improving the quality of the data, such as its completeness, 
  regularity and expressiveness.

  As these steps are very specific to each dataset, OpenSpending cannot 
  provide generic means to address these problems. Therefore, we aim to 
  document common patterns and practices with a specific focus on 
  governemnt finance.

* **Modeling, loading and aggregation of data.** After the data has been 
  brought into a clean and standardized form, it can be modeled to describe 
  its semantic structure in a multi-dimensional schema. Given such a model, 
  the data can be loaded into a store. A data store can then provide 
  further services, such as those aggregation operations commonly used in 
  OLAP systems used for enterprise business intelligence. Further services, 
  such as full-text search, can be used to augment the platform.

  OpenSpending aims to fully supply the technology needed to perform these
  tasks, both as a shared, web-based platform and as a software system that
  can be deployed as needed.

* **Display and annotation of data.** Given a data store platform, user- and
  topic-centric applications can be created to allow easy analysis of the 
  data. These applications can be both applicable onyl to a given dataset 
  (e.g. by focussing on visualizing the semantic relationship between specific 
  dimensions) or they can be generic. 

  Generic applications are key to the idea
  of OpenSpending, as they enable groups working on various datasets to share
  visualizations, browser compontents or other means of analyzing the data.

Using this approach we aim to make tracing the money simpler for those who
want to do it and we aim to provide the necessarily tools to enable both 
in-depth analysis of the data and the necessesary collaboration between 
different disciplines.


