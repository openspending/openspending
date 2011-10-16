var OpenSpending = OpenSpending || {};

OpenSpending.Model = function(customConfig) {
    var my = {
        config: {
            endpoint: "http://www.openspending.org/"
        }
    };
    if(customConfig){
        for(var key in customConfig){
            if(customConfig.hasOwnProperty(key)){
                my.config[key] = customConfig[key];
            }
        }
    }

    var datastore = OpenSpending.Datastore(my.config);
    var DataStoreModel = Backbone.Model.extend({
        url: function(){
            return my.config.endpoint + this.name + "/" + this.get("name");
        }
    });
    var DataStoreCollection = Backbone.Collection.extend({
        url: function(){
            return my.config.endpoint + this.name;
        },
        query: function(id, clb){
            var self = this;
            datastore.get(this.name, id, function(data){
                var obj = new self.model(data);
                self.add(obj);
                clb(obj);
            });
        }
    });
    
    // Model objects
    my.Dataset = DataStoreModel.extend({
        name: "dataset"
    });
    my.DatasetList = DataStoreCollection.extend({
        model: my.Dataset,
        name: "dataset"
    });

    my.Classifier = DataStoreModel.extend({
        name: "classifier",
        url: function(){
            return my.config.endpoint + this.name + "/" + this.get("taxonomy") + "/" + this.get("name");
        }
    });
    my.ClassifierList = DataStoreCollection.extend({
        model: my.Classifier,
        name: "classifier"
    });

    my.Entity = DataStoreModel.extend({
        name: "entity"
    });
    my.EntityList = DataStoreCollection.extend({
        model: my.Entity,
        name: "entity"

    });

    return my;
};
