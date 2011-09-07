var OpenSpending = OpenSpending || {};
/*
    Abstract the OpenSpending data store (accessed via its api).
    Sample use:
    
    var datastore = WDMMG.Datastore(other_config);
    datastore.list("entries", function(data){...});
    datastore.listEntries(function(data){...});
    datastore.filterDataset({key: value, foo: bar}, function(data){...});
    
*/

(function($) {
  var defaultConfig = {
    'apiUrl': 'http://openspending.org/api',
    'dataset': 'cra',
    'drilldowns': ['cofog1', 'cofog2', 'cofog3'],
    'cuts': ['year:2008'],
    'breakdown': 'region',
    'rootNodeLabel': 'Grant Total',
    'localApiCache': 'aggregate.json',
    'callback': function(tree) {  }
  };

  OpenSpending.Aggregator = function(customConfig) {
	var d = {
		config: customConfig ? customConfig : defaultConfig,
		/**
		 * Call the wdmmg aggregate api function (/api/2/aggregate)
		 * and build a tree that can be used by for the bubble charts
		 *
		 * @public getTree
		 *
		 * @param {string} api_url The url to the api,
		 * e.g. 'http://openspending.org/api'
		 * @param {string} dataset The name of the dataset, e.g. 'cra'
		 * @param {array} drilldowns the dimensions to drill down to, e.g.
		 * ['cofog1', 'cofog2', 'cofog3']
		 * @param {array} cuts (optional) The array with cuts, each element in the
		 * format 'key:value', e.g. ['time.from.year:2010']
		 * @param {function} callback A function that will accept the root node
		 * and builds the bubble chart.
		 * @param {object} testDataPath (optional) An object with json (not jsonp)
		 * test data. For testing only.
		 **/
		getTree: function() {
			//api_url, dataset, drilldowns, cuts, callback, testDataPath
			//construct the url
			var data = {},
				dataType = 'jsonp',
				url,
				config = this.config,
				drilldowns;
		
			url = config.apiUrl + '/2/aggregate';
			data.dataset = config.dataset;
			data.drilldown = config.drilldowns.join('|');
			data.order = config.order.join('|');
		
			if (config.cuts !== undefined) {
				data.cut = config.cuts.join('|');
			}
		
			// add an optional breakdown to drilldowns to query the api
			drilldowns = config.drilldowns.slice(); //copy
		
			if (config.breakdown !== undefined) {
				drilldowns.push(config.breakdown);
			}
			drilldowns = $.unique(drilldowns);
			data.drilldown = drilldowns.join('|');
		
			if (config.localApiCache !== undefined) {
				url = config.localApiCache;
				dataType = 'json';
			}
			$.ajax({
				url: url,
				data: data,
				dataType: dataType,
				context: this,
				success: this.onJSONTreeLoaded
			});
		},
		/**
		 * 
		 *
		 */
		onJSONTreeLoaded: function(data) {
			var tree = this.buildTree(data);
			if ($.isFunction(this.config.callback)) {
				this.config.callback(tree);
			}
		},
		
		/**
		 * Build a tree form the drill down entries
		 *
		 * @public buildTree
		 *
		 * @param {object} data The json object responded from the
		 * aggregate api.
		 * @param {array} drilldowns List of drilldown criteria (strings)
		 * @param {object} rootNode (optional) Pass an object with properties
		 * for the root node. Maybe you want to set 'color' (default: #555) or
		 * the 'label' (default: 'Total')
		 **/
		buildTree: function(data) {
			var entries = data.drilldown,
			    config = this.config,
				drilldowns = config.drilldowns,
				breakdown = config.breakdown,
				rootNode = { label: config.rootNodeLabel },
				nodes = {},
				root = {id: 'root',
						label: 'Total',
						color: '#555',
						amount: 0.0,
						children: [],
						level: 0,
					   breakdowns: {}};
			
			if (rootNode !== undefined) {
				// extend root with the properties of rootNode
				$.extend(true, root, rootNode);
			}
			nodes.root = root;
			
			for (var i in drilldowns) {
				var drilldown = drilldowns[i];
				nodes[drilldown] = {};
			}
			if (data.errors !== undefined) {
				throw "Error";
			}
			
			for (var index in entries) {
				this.processEntry(entries[index], nodes);
				
			}
		
			return nodes.root;

		},
		processEntry: function(entry, nodes) {
            var parent = nodes.root,
                level = 0,
                drilldown,
                drilldowns = this.config.drilldowns,
                current,
                node,
                node_template;
    
            
            for (var index in drilldowns) {
                drilldown = drilldowns[index];
    
                level = level + 1;
                current = entry[drilldown];
                node_template = this.toNode(current, parent);
    
                node = nodes[node_template.id];
                if(node === undefined) {
                    // Initialize a new node and add it to the parent node
                    node = node_template;
                    node.children = [];
                    node.amount = 0.0;
                    node.color = current ? current.color : undefined;
                    node.level = level;
                    node.breakdowns = {};
                    parent.children.push(node);
                    nodes[node.id] = node;
                }
    
                node.amount = node.amount + entry.amount;
    
                // Add the current amount and the breakdown to the root node
                // to have a total.
                if(level === 1) {
                    nodes.root.amount = nodes.root.amount + entry.amount;
                    this.addBreakdown(nodes.root, entry);
                }
    
                // update the breakdown for the current node
                this.addBreakdown(node, entry);
                parent = node;
            }
        },
        /**
         *  Add a node for each drilldown to the 'nodes' object
         *  Process the nodes to have:
         *  * The summed up amount
         *  * A children array
         *  * A color property
         *  * An unique id
         *
         *  @method processEntry
         *  @param {object} entry The entry in the list of drill downs
         *  @param {object} node The node to which we save the breakdown
         *  @return {undefined}
         */
        addBreakdown: function(node, entry) {
            var breakdown = this.config.breakdown;
            if (breakdown === undefined) {
                
                return;
            }
    
            var breakdown_value,
                breakdown_node,
                node_template,
                nodes = {},
                _id;
            breakdown_value = entry[breakdown];
            node_template = this.toNode(breakdown_value);
            _id = node_template.id;
            breakdown_node = node.breakdowns[_id];
            if (breakdown_node === undefined) {
                breakdown_node = node_template;
                node.breakdowns[_id] = breakdown_node;
            }
            breakdown_node.amount = breakdown_node.amount + entry.amount;
           
            
        },
        toNode: function(value, parent) {
            var type = typeof(value),
                id,
                label,
                prefix,
                taxonomy,
                name;
        
            prefix = parent ? parent.id + '__' : '';
            if (value === undefined || value === null) {
                id = 'others';
                label = 'Others';
                name = 'others';
            } else if (type === 'object') {
                if (value._id === undefined) {
                    id = 'others';
                    label = 'Others';
                    name = 'others';
                } else {
                    id = value._id;
                    label = value.label;
                    taxonomy = value.taxonomy;
                    name = value.name;
                    if (!name) {
                        if (label) {
                            name = label.toLowerCase().replace(/\W/g, "-");
                        } else {
                            name = id;
                        }
                    }
                }
            } else if ( type === 'boolean' ) {
                if (value) {
                    id = 'yes';
                    label = 'Yes';
                    name = 'yes';
                } else {
                    id = 'no';
                    label = 'No';
                    name = 'no';
                }
            } else if ( type === 'string' || type === 'number') {
                id = value + '';
                label = value + '';
                name = id.toLowerCase().replace(/\W/g, "-");
            } else {
                throw 'unsupported type: ' + type;
            }
            return {id: prefix + id,
                    label: label,
                    name: name,
                    taxonomy: taxonomy,
                    amount: 0.0};
        }
	};
	d.getTree();
};

}(jQuery));