
initModelEditor = function($, datasetName, meHook, fallbackHook) {
  var modelEditor = $(meHook);

  var gotAnalysis = function(data) {
	var columns = data.columns; // FIXME: might be absent

	config = { columns: columns,
	           getEditor: findEditor };
	modelEditor.modelEditor(config);

	var me = $(meHook).data('modelEditor');
	$(fallbackHook).change(function () {
      me.data = JSON.parse($(this).val());
      $(meHook).trigger('modelChange');
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
