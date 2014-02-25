(function ($) {

    // Choropleth function to create the map for the given dom element with
    // the given options
    $.choropleth = function ( element, options ) {
	// Get the configuration
	var config = $.extend(true, {}, $.choropleth.defaults,
			      $.choropleth.domopts(element), options);

	// Create the map
	var map = $K.map(element, config.width, config.height);

	// Load the map
	map.loadMap(config.map.url, function(map) {
	    // Get the datasets via jsonp
	    $.ajax({
		url: config.data.url,
		dataType: "jsonp",
		success: function(resp) {
		    // Fill in the intensity (count) for each id (territory)
		    var d1 = {};
		    $.each(config.data.objects(resp), function(i, obj) {
			d1[config.data.id(obj)] = config.data.intensity(obj);
		    });

		    // Add background map layer
		    map.addLayer({
			id: config.map.group,
			className: 'bg',
			key: config.map.id,
			filter: function(d) {
			    return !d1.hasOwnProperty(d[config.map.id]);
			}
		    });
		    
		    // Add foreground map layer
		    map.addLayer({
			id: config.map.group,
			key: config.map.id,
			filter: function(d) {
			    return d1.hasOwnProperty(d[config.map.id]);
			}
		    });

		    // Create the choropleth (this method is obsolote in
		    // newer versions of kartograph.js)
		    map.choropleth({
			data: d1,
			colors: function(d) {
			    // Color of svg object (territory)
			    if (d === null) return '#fff';
			    return config.colorscale.getColor(d);
			},
			duration: function(d) {
			    // For how long should it fade in
			    return Math.min(900,300*d)
			},
			delay: function(d) { 
			    // When should it fade in
//			    return 100 + 200*(10-d)+Math.random()*300
			}
		    });
		    
		    // Whe one clicks on a path (territory) config defines
		    // what should happen
		    map.onLayerEvent('click', function(d) {
			config.click(d);
		    });
		}
	    });
	}, { padding: 5 });
    }

    // Define the choropleth defaults which define the world map of all
    // datasets in OpenSpending (default map is the front page map of
    // openspending.org
    $.choropleth.defaults = {
	width: 640, // Width of choropleth map
	height: 320, // Height of choropleth map
	data: {
	    url: 'https://openspending.org/datasets.json', // Default OS datasets
	    objects: function(e) { return e.territories }, // Object list
	    intensity: function(e) { return e.count }, // How intense?
	    id: function(e) { return e.code } // Identifier in data and map
	},
	map: {
	    url:'https://openspending.org/static/openspendingjs/app/spending-map/world.svg', // Default to world map from OS
	    group: 'regions', // Default to group in OS world map
	    id: 'iso2', // Identifier of path in map (same value as data.id)
	},
	click: function(e) {}, // Default behaviour of clicking is nothing
	colorscale: new chroma.ColorScale({  // Default colorscale is green
	    colors: chroma.brewer.Greys.reverse(),    // (overwrite needs to have a
	    limits: [-2,-1,0,1,2,3,4,5,6,7]  // getColor function (like chroma)
	})
    };

    // HTML5 data configurations. The dom element is passed into the function
    // and returns an object with properties that can overwrite the default
    // ones (defined above). The only properties that cannot be defined are
    // 'click' and 'colorscale' which are javascript based.
    // 'data.objects', 'data.intensity' and 'data.id' are all functions that
    // fetch a property by the name defined by the html5 data variable
    // 'data.objects' from the dataset json response and 'data.intensity' and
    // 'data.id' from each object in 'data.objects'
    $.choropleth.domopts = function( element ) {
	return {
	    width: $(element).attr('data-map-width'),
	    height: $(element).attr('data-map-height'),
	    data: {
		url: $(element).attr('data-url'),
		objects: $(element).attr('data-objects') ?
		    function(e) {
			return e[$(element).attr('data-objects')];
		    } : undefined,
		intensity: $(element).attr('data-impact') ? 
		    function(e) { 
			return e[$(element).attr('data-impact')];
		    } : undefined,
		id: $(element).attr('data-id') ?
		    function(e) {
			return e[$(element).attr('data-id')];
		    } : undefined
	    },
            map: {
		url: $(element).attr('data-map-url'),		
		group: $(element).attr('data-map-group'),
		id: $(element).attr('data-map-path-id')
	    }
	}	     
    };

    // Extend jquery's prototype with the choropleth function that runs through
    // all dom elements and passes them, along with the options to the
    // choropleth function
    $.fn.extend({
	choropleth: function(options) {
	    if(options == undefined) options = {};
	    this.each(function() {
		$.choropleth( this, options);
	    });
	}
    });

    // On load we automatically apply choropleth to all dom elments that have
    // the 'choropleth' class
    $('.choropleth').choropleth();

}(jQuery));
