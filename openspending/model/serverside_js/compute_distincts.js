// aggregate all distinct values for top level properties for all entries
// in a dataset and save them into a collection named
// 'distincts__<dataset_name>'. For the time property, the values
// for time.[to,from][day,month,year] are added instead of the
// 'time' object.
//
// The documents in the collection have the following structure:
// {_id: <the value>, {value: {keys: [<key>, ...]}}}
// where _id is the value stored in an entry and 'value.keys' are all
// keys where the value is used.
// To find all distinct values for a certain key in the entry documents
// query the dedicated collection for {'value.keys': key} and use all
// values for _id.

function(dataset_name) {

    // validate input
    if (dataset_name === undefined) {
        throw "dataset_name is required";
    }
    if (db.dataset.findOne({name: dataset_name}) === null) {
        throw 'A dataset named "' + dataset_name + '" does not exist';
    }

    // target colection name and index
    var collection_name = 'distincts__' + dataset_name;
    var collection = db[collection_name];
    collection.ensureIndex({'value.keys': 1});


    var _map = function() {
        // the same keys are used in openspending.logic.entry.distinct
        var known = ['_id', 'name', 'amount', '_aggregation',
                     'classifiers', 'entities', 'currency'];

        for (key in this) {
            if (known.indexOf(key)>-1) {
                continue;
            }
            if (key === 'time') {
                emit(this.time.from.year, {keys: ['time.from.year']});
                emit(this.time.from.month, {keys: ['time.from.month']});
                emit(this.time.from.day, {keys: ['time.from.day']});
                emit(this.time.to.year, {keys: ['time.to.year']});
                emit(this.time.to.month, {keys: ['time.to.month']});
                emit(this.time.to.day, {keys: ['time.to.day']});
            }
            else {
                emit(this[key], {keys: [key]});
            }
        };
    };

    var _reduce = function(value, emitted_keys) {
        var result = {keys: []};
        emitted_keys.forEach(function(emitted) {
            emitted.keys.forEach(function(key){
                if (result.keys.indexOf(key) === -1) {
                    result.keys.push(key);
                }
            });
        });
        return result;
    };

    return db.entry.mapReduce(_map, _reduce,
                              {
                                  out: collection_name,
                                  query: {'dataset.name': dataset_name}
                              });
};
