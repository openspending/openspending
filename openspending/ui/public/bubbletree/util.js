
BubbleTree.Utils.formatNumber = function(n) {
	var prefix = '';
	if (0 >= n) {
		n = n*-1;
		prefix = '-';
	}
	if (n >= 1000000000000) return prefix+Math.round(n / 1000000000) + 'G';
	if (n >= 1000000000) return prefix+Math.round(n / 100000000)/10 + 'G';
	if (n >= 1000000) return prefix+Math.round(n / 100000)/10 + 'M';
	if (n >= 1000) return prefix+Math.round(n / 100)/10 + 'k';
	else return prefix+n;
};


var getTooltip = function() {
	return this.getAttribute('tooltip');
};

var initTooltip = function(node, domnode) {
	domnode.setAttribute('tooltip', node.label+' &nbsp;<b>'+node.famount+'</b><br /><small>'+node.name+'</small>');
	
	vis4.log(domnode.getAttribute('tooltip'));
				
	$(domnode).tooltip({ delay: 200, bodyHandler: getTooltip });
};

var createBubbles = function(apiUrl, dataset, drilldowns, breakdown, breakdown_styles) {
	
	new OpenSpending.Aggregator({
		apiUrl: apiUrl,
		dataset: dataset,
		drilldowns: drilldowns,
		order: [ drilldowns[0] + ':asc' ],
		rootNodeLabel: 'Total',
		breakdown: breakdown,
		callback: function(data) {
			
			new BubbleTree({
				data: data,
				container: '.bubbletree',
				bubbleType: 'donut',
				initTooltip: initTooltip,
				maxNodesPerLevel: 12,
				bubbleStyles: {									
					'id': {
						'root': { color: '#ffffff' }
					},
					'name': breakdown_styles							
				}
			});
		}
	});
	
};