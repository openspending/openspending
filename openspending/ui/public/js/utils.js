var DEBUG;

function debug(message) {
	var console = window['console'];
	if (console && console.log) {
	console.log(message);
	}
}

var OpenSpending = OpenSpending || {};
OpenSpending.Utils = OpenSpending.Utils || {};

OpenSpending.Utils.roundNumber = function(num, dec) {
	return Math.round(num*Math.pow(10,dec))/Math.pow(10,dec);
}

OpenSpending.Utils.formatAmount = function(num) {
    var billion = 1000000000;
    var million = 1000000;
    var thousand = 1000; 
    var numabs = Math.abs(num);
    if (numabs > billion) {
        return OpenSpending.Utils.roundNumber(num / billion, 2) + 'bn';
    }
    if (numabs > (million/2)) {
        return OpenSpending.Utils.roundNumber(num/million, 2) + 'm';
    }
    if (numabs > thousand) {
        return OpenSpending.Utils.roundNumber(num/thousand, 2) + 'k';
    } else {
        return num; 
    }
};

/*
	Parse a URL query string (?xyz=abc...) into a dictionary.
*/
function parseQueryString() {
	var q = arguments.length > 0 ? arguments[0] : window.location.search.substring(1);
	var urlParams = [],
		e,
		d = function (s) { return unescape(s.replace(/\+/g, " ")); },
		r = /([^&=]+)=?([^&]*)/g;

	while (e = r.exec(q)) {
		urlParams.push([d(e[1]), d(e[2])]);
	}
	return urlParams;
}

/*
Write tabular data as HTML table.

	:tabular: tabular data object (dict with header and data keys).
	:options: optional keyword arguments:
		colTypes: types of columns keyed by column name
		displayNames: ditto for display names for columns
*/
writeTabularAsHtml = function(tabular) {
	var options = {};
	if (arguments.length > 1) {
		options = arguments[1];
	}
	var colTypes = {};
	var displayNames = {};
	if (options.colTypes) {
		colTypes = options.colTypes;
	}
	if (options.displayNames) {
		displayNames = options.displayNames;
	}
	// knows how to format and justify based on combination of col type labelling (via colTypes)
	// and value based logic
	var _ColType=[];
	var _thead = $('<thead></thead>');
	$.each(tabular.header, function(i,col) {
		var tempDisplayName = displayNames[col] ? displayNames[col] : col;
		_thead.append($('<th></th>').append(tempDisplayName));
		if (colTypes[col]) {
			_ColType[i]=colTypes[col];
		}
	});
	var _tbody = $('<tbody></tbody>');
	// var red = /^(19|20)\d{2}$/; - replaced by _ColType
	// var rep = /^([\d\.\-]+)\%$/; - replaced by _ColType
	var ren = /^[\d\.\-]+$/;
	var reb = /^$/;
	$.each(tabular.data, function(i,row) {
	var _newrow = $('<tr></tr>');
	$.each(row, function(j, cell) {
		// decide action depending on type
		var cell2;
		if(_ColType[j] == 'range'){
		// year range
		var cell3 = parseFloat(cell);
		cell3++;
		cell2=cell+'-'+cell3;
		   	_newrow.append($('<td></td>').append(cell2));
		}else if(reb.test(cell)){
		// blank
		cell2='';
		_newrow.append($('<td></td>').append(cell2));
		}else if(_ColType[j] == 'percent'){
		// percent
		// 20.5% saved as 0.205. Converted back here to 20.5%
		var cell3=cell*100;
		cell2=cell3.toFixed(1)+'%';
		_newrow.append($('<td class="amount"></td>').append(cell2));
		}else if(ren.test(cell)){
		// number
		var cell3=parseFloat(cell);
		cell2=cell3.toFixed(0);
		_newrow.append($('<td class="amount"></td>').append(cell2));
		}else{
		// other
		cell2=cell;
		_newrow.append($('<td></td>').append(cell2));
		}
	});
	_tbody.append(_newrow);
	});
	return {'thead': _thead, 'tbody': _tbody};
}

function loadingMessage() {
	$.blockUI({
		message: 'Please wait, loading ...',
		timeout: 30000,
		css: { 
			border: 'none', 
			padding: '15px', 
			backgroundColor: '#000', 
			'-webkit-border-radius': '10px', 
			'-moz-border-radius': '10px', 
			opacity: .5, 
			color: '#fff' 
		}
	}); 
	$('.blockMsg').attr('title','Click to unblock').click($.unblockUI); 
}

