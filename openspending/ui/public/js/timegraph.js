function suffixFormatter(val, axis) {
    if (Math.abs(val) > 1000000000)
      return (val / 1000000000).toFixed(1) + " b";
    if (Math.abs(val) > 1000000)
      return (Math.abs(val) / 1000000).toFixed(1) + " m";
    else if (Math.abs(val) > 1000)
      return (val / 1000).toFixed(1) + " k";
    else
      return val.toFixed(1);
}

$(function () {
	var previousPoint = null;
	$("#timegraph").bind("plothover", function (event, pos, item) {
		$("#x").text(pos.x.toFixed(2));
		$("#y").text(pos.y.toFixed(2));

		if (item) {
			if (previousPoint != item.datapoint) {
				previousPoint = item.datapoint;
				
				$("#tooltip").remove();
                var date = new Date(item.datapoint[0]);
				var x = date.getDate() + "." + (date.getMonth()+1) + "." + date.getFullYear();
                var y = suffixFormatter(item.datapoint[1]);
				showTooltip(item.pageX, item.pageY,
							"Sum of " + y + " on " + x);
			}
		}
		else {
			$("#tooltip").remove();
			previousPoint = null;            
		}
	});
});

function showTooltip(x, y, contents) {
	$('<div id="tooltip">' + contents + '</div>').css( {
		position: 'absolute',
		display: 'none',
		top: y + 1,
		left: x + 1,
		border: '1px solid #fdd',
		padding: '2px',
		'background-color': '#fee',
		opacity: 0.80
	}).appendTo("body").fadeIn(200);
}
 

