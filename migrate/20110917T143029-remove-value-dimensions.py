import logging

from openspending.lib import cubes
from openspending import migration, model, mongo

log = logging.getLogger(__name__)

def up():
    group_args = ({'dataset':1}, {}, {'num': 0},
                  'function (x, acc) { acc.num += 1 }')

    before = mongo.db.dimension.group(*group_args)
    dims = model.dimension.find({'type': {'$nin': ['entity', 'classifier']}})
    for d in dims:
        log.info("Removing dimension: %s", d)
        model.dimension.remove({'_id': d['_id']})
    after = mongo.db.dimension.group(*group_args)

    for bf, af in zip(before, after):
        if int(bf['num']) != int(af['num']):
            log.warn("Number of dimensions for dimension '%s' "
                     "changed. Recomputing cubes.", bf['dataset'])
            ds = model.dataset.find_one({'name': bf['dataset']})
            cubes.Cube.update_all_cubes(ds)

def down():
    raise migration.IrreversibleMigrationError("Can't add back dimension "
                                               "fields that we dropped!")