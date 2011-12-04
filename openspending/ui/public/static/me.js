
initModelEditor = function(datasetName, $) {
  var modelEditor = $('#m1');

  var gotAnalysis = function(data) {
	var columns = ['date', 'value', 'dept_id', 'dept_name', 'dept_transaction_id', 'recipients', 'cofog_code_l1'];
	var columns = data.columns; // FIXME: might be absent

	config = { columns: columns,
	           getEditor: findEditor };
	modelEditor.modelEditor(config);

	var me = $('#m1').data('modelEditor');
	$('#fallback').change(function () {
      me.data = JSON.parse($(this).val());
      $('#m1').trigger('modelChange');
	});
  };

  var gotSources = function(data) {

	if(data.length === 0) {
	  alert("No analyses of data found");
	  return;
	};
	var last = data[data.length - 1];
	$.ajax({
	  url: '/' + datasetName + '/sources/' + last.id + '/analysis.json',
	  dataType: 'json',
	  success: gotAnalysis
	});
  };

  $.ajax({
	url: '/' + datasetName + '/sources.json',
	dataType: 'json',
	success: gotSources
  });
};
