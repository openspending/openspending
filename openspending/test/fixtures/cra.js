{
  "dataset": {
    "name": "cra",
    "label": "Country Regional Analysis v2009",
    "description": "The Country Regional Analysis published by HM Treasury (2010 version).\n\nSource data can be found in the [CKAN data package](http://ckan.net/package/ukgov-finances-cra)",
    "territories": [
      "GB"
    ],
    "currency": "GBP"
  },
  "mapping": {
    "from": {
      "type": "entity",
      "attributes": {
        "name": {"column": "from.name", "datatype": "string"},
        "label": {"column": "from.label", "datatype": "string"},
        "description": {"column": "from.description", "datatype": "string", 
          "default_value": ""}
      },
      "label": "Paid by",
      "description": "The entity that the money was paid from."
    },
    "to": {
      "type": "entity",
      "attributes": {
        "name": {"column": "to.name", "datatype": "string"},
        "label": {"column": "to.label", "datatype": "string"},
        "description": {"column": "to.description", "datatype": "string"}
      },
      "label": "Paid to",
      "description": "The entity that the money was paid to"
    },
    "time": {
      "type": "value",
      "column": "time.from.year",
      "label": "Tax year",
      "description": "The accounting period in which the spending happened",
      "datatype": "date"
    },
    "amount": {
      "column": "amount",
      "label": "",
      "description": "",
      "datatype": "float",
      "type": "value"
    },
    "total": {
      "column": "amount",
      "label": "",
      "description": "",
      "datatype": "float",
      "type": "measure"
    },
    "cap_or_cur": {
      "column": "cap_or_cur",
      "label": "CG, LG or PC",
      "description": "Central government, local government or public corporation",
      "datatype": "string",
      "type": "value"
    },
    "region": {
      "column": "region",
      "label": "Region",
      "description": "",
      "datatype": "string",
      "type": "value",
      "facet": true
    },
    "name": {
      "column": "name",
      "label": "Name",
      "description": "",
      "datatype": "string",
      "type": "value",
      "key": true
    },
    "currency": {
      "column": "currency",
      "label": "Currency",
      "description": "",
      "datatype": "string",
      "type": "value"
    },
    "population2006": {
      "column": "population2006",
      "label": "Population in 2006",
      "description": "",
      "datatype": "float",
      "type": "value"
    },
    "pog": {
      "type": "classifier",
      "attributes": {
        "name": {"column": "pog.name", "datatype": "string"},
        "label": {"column": "pog.label", "datatype": "string"}
      },
      "label": "Programme Object Group",
      "taxonomy": "pog"
    },
    "cofog1": {
      "type": "classifier",
      "attributes": {
        "name": {"column": "cofog1.name", "datatype": "string", 
          "default_value": "XX"},
        "label": {"column": "cofog1.label", "datatype": "string", 
          "default_value": "(Undefined)"},
        "description": {"column": "cofog1.description", "datatype": "string", 
          "default_value": ""},
        "level": {"column": "cofog1.level", "datatype": "string", 
          "default_value": ""},
        "change_date": {"column": "cofog1.change_date", "datatype": "string", 
          "default_value": ""}
      },
      "label": "COFOG level 1",
      "description": "Classification Of Function Of Government, level 1",
      "taxonomy": "cofog",
      "facet": true
    },
    "cofog2": {
      "type": "classifier",
      "attributes": {
        "name": {"column": "cofog2.name", "datatype": "string", 
          "default_value": "XX.X"},
        "label": {"column": "cofog2.label", "datatype": "string", 
          "default_value": "(Undefined)"},
        "description": {"column": "cofog2.description", "datatype": "string", 
          "default_value": ""},
        "level": {"column": "cofog2.level", "datatype": "string", 
          "default_value": ""},
        "change_date": {"column": "cofog2.change_date", "datatype": "string", 
          "default_value": ""}
      },
      "label": "COFOG level 2",
      "description": "Classification Of Function Of Government, level 2",
      "taxonomy": "cofog"
    },
    "cofog3": {
      "type": "classifier",
      "attributes": {
        "name": {"column": "cofog3.name", "datatype": "string", 
          "default_value": "XX.X.X"},
        "label": {"column": "cofog3.label", "datatype": "string", 
          "default_value": "(Undefined)"},
        "description": {"column": "cofog3.description", "datatype": "string", 
          "default_value": ""},
        "level": {"column": "cofog3.level", "datatype": "string", 
          "default_value": ""},
        "change_date": {"column": "cofog3.change_date", "datatype": "string", 
          "default_value": ""}
      },
      "label": "COFOG level 3",
      "description": "Classification Of Function Of Government, level 3",
      "taxonomy": "cofog"
    }
  },
  "views": [
    {
      "entity": "dataset",
      "label": "Spending by primary function",
      "name": "default",
      "dimension": "dataset",
      "breakdown": "cofog1",
      "filters": {"name": "cra"}
    },
    {
      "entity": "dataset",
      "label": "Spending by region",
      "name": "region",
      "dimension": "dataset",
      "breakdown": "region",
      "filters": {"name": "cra"}
    },
    {
      "entity": "classifier",
      "label": "Spending by region (within primary function)",
      "name": "default",
      "dimension": "cofog1",
      "breakdown": "region",
      "filters": {"taxonomy": "cofog"}
    },
    {
      "entity": "entity",
      "label": "Spending by region (within department)",
      "name": "default",
      "dimension": "from",
      "breakdown": "region",
      "filters": {"gov_department": "true"}
    }
  ]
}
