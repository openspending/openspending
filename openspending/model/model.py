from openspending.model.changeset import Revisioned
from openspending.model.mongo import dictproperty

default_mapping = {
    "time": {
        "label": "Time",
        "type": "value",
        "column": "date",
        "datatype": "date"
        },
    "amount": {
        "label": "Amount",
        "type": "value",
        "column": "amount",
        "datatype": "float"
        },
    "from": {
        "label": "Paid by",
        "type": "entity",
        "fields": [
            {"column": "from_id", "name": "name", "datatype": "id"},
            {"column": "from_label", "name": "label", "datatype": "string"}
            ]
        },
    "to": {
        "label": "Paid to",
        "type": "entity",
        "fields": [
            {"name": "name", "constant": "society", "datatype": "constant"},
            {"name": "label", "constant": "Society", "datatype": "constant"}
            ]
        }
    }


class Model(Revisioned):

    id = dictproperty('_id')
    author = dictproperty('author')
    time = dictproperty('time')
    dataset = dictproperty('dataset')
    mapping = dictproperty('mapping')
