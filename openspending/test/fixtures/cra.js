{
  "dataset": {
    "model_rev": 1,
    "name": "cra",
    "label": "Country Regional Analysis v2009",
    "description": "The Country Regional Analysis published by HM Treasury (2010 version).\n\nSource data can be found in the [CKAN data package](http://ckan.net/package/ukgov-finances-cra)",
    "currency": "GBP",
    "unique_keys": ["name"]
  },
  "mapping": {
    "from": {
      "type": "entity",
      "fields": [
        {"column": "from.name", "datatype": "string", "name": "name"},
        {"column": "from.label", "datatype": "string", "name": "label"},
        {"column": "from.description", "datatype": "string", "name": "description"}
      ],
      "label": "Paid by",
      "description": "The entity that the money was paid from."
    },
    "to": {
      "type": "entity",
      "fields": [
        {"column": "to.name", "datatype": "string", "name": "name"},
        {"column": "to.label", "datatype": "string", "name": "label"},
        {"column": "to.description", "datatype": "string", "name": "description"}
      ],
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
      "type": "value"
    },
    "name": {
      "column": "name",
      "label": "Name",
      "description": "",
      "datatype": "string",
      "type": "value"
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
      "fields": [
        {"column": "pog.name", "datatype": "string", "name": "name"},
        {"column": "pog.label", "datatype": "string", "name": "label"}
      ],
      "label": "Programme Object Group",
      "taxonomy": "pog"
    },
    "cofog1": {
      "type": "classifier",
      "fields": [
        {"column": "cofog1.name", "datatype": "string", "name": "name"},
        {"column": "cofog1.label", "datatype": "string", "name": "label"},
        {"column": "cofog1.description", "datatype": "string", "name": "description"},
        {"column": "cofog1.level", "datatype": "string", "name": "level"},
        {"column": "cofog1.change_date", "datatype": "string", "name": "change_date"}
      ],
      "label": "COFOG level 1",
      "description": "Classification Of Function Of Government, level 1",
      "taxonomy": "cofog"
    },
    "cofog2": {
      "type": "classifier",
      "fields": [
        {"column": "cofog2.name", "datatype": "string", "name": "name"},
        {"column": "cofog2.label", "datatype": "string", "name": "label"},
        {"column": "cofog2.description", "datatype": "string", "name": "description"},
        {"column": "cofog2.level", "datatype": "string", "name": "level"},
        {"column": "cofog2.change_date", "datatype": "string", "name": "change_date"}
      ],
      "label": "COFOG level 2",
      "description": "Classification Of Function Of Government, level 2",
      "taxonomy": "cofog"
    },
    "cofog3": {
      "type": "classifier",
      "fields": [
        {"column": "cofog3.name", "datatype": "string", "name": "name"},
        {"column": "cofog3.label", "datatype": "string", "name": "label"},
        {"column": "cofog3.description", "datatype": "string", "name": "description"},
        {"column": "cofog3.level", "datatype": "string", "name": "level"},
        {"column": "cofog3.change_date", "datatype": "string", "name": "change_date"}
      ],
      "label": "COFOG level 3",
      "description": "Classification Of Function Of Government, level 3",
      "taxonomy": "cofog"
    }
  }
}
