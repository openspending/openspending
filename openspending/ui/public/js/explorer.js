/*global window: true, pv: true, $: true, jQuery: true, Backbone: true */

var OpenSpending = OpenSpending || {};

OpenSpending.Explorer = {
    View: {},
    Controller: {},
    init: function(config) {
        var e = new OpenSpending.Explorer.Controller(config);
        Backbone.history.start();
        return e;
    }
};

var initExplorer = function(containerId, customConfig) {
  // customConfig.container = $('#'+container_id);
  //return OpenSpending.Explorer.init(customConfig);

  var $breakdown = $('#controls-breakdown');
  var $breakdownList = $breakdown.find('ol');
  var model = OpenSpending.Model(customConfig);

  var datasetObj = new model.Dataset({
    name: customConfig.dataset
    });
  datasetObj.fetch({
    success: init
    });

  function init(dataset) {
    customConfig.drilldownDimensions = dataset.drilldownDimensions();
    $.each([1,2], function(idx, item) {
      var tselect = $('<select />');
      $.each(customConfig.drilldownDimensions, function(idx, item) {
        tselect.append($('<option />').attr('value', item).html(item));
      });
      $breakdownList.append($('<li />').append(tselect));
    });
    $breakdown.find('button').click(function(e) {
      e.preventDefault();
      draw();
    });
    draw();
  }

  function draw() {
    var vals = [];
    $.each($breakdown.find('select option:selected'), function(idx, item) {
      var _dim = $(item).text();
      vals.push(_dim);
    });
    vals = _.uniq(vals);
    customConfig.drilldowns = vals;
    renderTree(containerId, customConfig);
  }

};

function renderTree(figId, customConfig) {
  var $tooltip = $('<div class="tooltip">Tooltip</div>');
  $(figId).append($tooltip);
  
  var tooltip = function(event) {
    if (event.type == 'SHOW') {
      // show tooltip
      vis4.log(event);
      $tooltip.css({ 
        left: event.mousePos.x + 4, 
        top: event.mousePos.y + 4 
      });
      $tooltip.html(event.node.label+' <b>'+event.node.famount+'</b>');
      var bubble = event.target;
      
      $tooltip.show();
    } else {
      // hide tooltip
      $tooltip.hide();
    }
  };
  var yearChange = function(year) { window.alert('year changed to '+year); };

  var config = {
    apiUrl: customConfig.endpoint + 'api',
    dataset: customConfig.dataset,
    drilldowns: customConfig.drilldowns,
    // cuts: [],
    rootNodeLabel: 'Total',

    container: figId,
    initYear: 2011,
    // breakdown
    //breakdown: 'cofog3',
    // this callback is invoked as soon as the year changes by url
    // defines what class is used to render the bubbles
    // possible values are pie,donut,plain,multi
    bubbleType: ['plain', 'plain', 'plain']
  };

  // config is now defined in separate files
  vis4.log(config);
  
  config.tooltipCallback = tooltip;
  config.yearChangeHandler = yearChange;
  
  config.bubbleStyles = {
    // the taxonomy "id" is actually not a real taxonomy,
    // but a fallback to access nodes w/o taxonomy by
    // their id
    'id': {
      'root': { icon: 'icons/pound.svg' }
    }
  };
  
  new OpenSpending.BubbleTree.Loader(config);
}	
