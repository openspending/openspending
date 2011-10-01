from openspending import mongo
from .. import helpers as h

def test_serverside_js_loaded():
    h.assert_true('compute_distincts' in mongo.db.system_js.list(),
                  "'compute_distincts' serverside JS not loaded\!")