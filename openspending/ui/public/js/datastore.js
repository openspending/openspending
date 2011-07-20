var OpenSpending = OpenSpending || {};
/*
    Abstract the OpenSpending data store (accessed via its api).
    Sample use:
    
    var datastore = OpenSpending.Datastore(other_config);
    datastore.list("entries", function(data){...});
    datastore.listEntries(function(data){...});
    datastore.filterDataset({key: value, foo: bar}, function(data){...});
    
*/

OpenSpending.Datastore = (function($){
    var defaultConfig = {
            // dataStoreApi: 'http://data.wheredoesmymoneygo.org/api',
            'endpoint': 'http://localhost:5000/'
    };
    return function(customConfig){
        var breakdown = {},
            keys = {},
            resources = ["Entry", "Entity", "Classifier", "Dataset"],
            resourceOperations = ["list", "get", "filter"],
            CLB = "?callback=?";
        
        var d = {
            getData: function(path, data, callback){
                return $.ajax({
                  url: this.config.endpoint + path + CLB,
                  dataType: 'json',
                  data: data,
                  success: callback,
                  cache: true
                });
            },
            config: customConfig || defaultConfig,
            list: function(resource, callback){
                this.getData(resource, {}, callback);
            },
            get: function(resource, objectId, callback){
                this.getData(resource + "/" + objectId, {}, callback);
            },
            filter: function(resource, filters, callback){
                this.getData(resource, filters, callback);
            },
            aggregate: function(slice, breakdownKeys, callback) {
                var breakdown = {"slice": slice},
                    keys = [];
                if (breakdownKeys){
                    keys = breakdownKeys.slice();
                }
                // sort the keys as order does not matter for aggregation
                // canonical string for cache?
                keys.sort();

                for (var i=0; i< keys.length; i++){
                    breakdown["breakdown-"+keys[i]] = "yes";
                }
                // probably better API URL:
                // $.getJSON(this.config+resource+"/aggregate"+CLB, breakdown, callback);
                this.getData("api/aggregate", breakdown, callback);
            }
        };
        
        /* Curry fancy shortcut methods like getEntry, filterClassifier etc. */
        for(var i=0; i<resources.length; i++){
            for (var j=0; j<resourceOperations.length; j++){
                (function(resource, operation){
                    d[operation+resource] = function(){
                        return d[operation].apply(d, [resource.toLowerCase()].concat(Array.prototype.slice.call(arguments)));
                    };
                }(resources[i], resourceOperations[j]));
            }
        }
        return d;
    };
}(jQuery));
