
initModelEditor = function($, config) {
  var $modelEditor = $(config.editorSelector);
  var fallbackHook = config.fallbackSelector;

  var gotAnalysis = function(data) {
	var columns = data.columns; // FIXME: might be absent

	config = { columns: columns,
	           getEditor: findEditor };
	$modelEditor.modelEditor(config);

	var me = $modelEditor.data('modelEditor');
	$(fallbackHook).change(function () {
      me.data = JSON.parse($(this).val());
      $modelEditor.trigger('modelChange');
	});
  };

  var gotSources = function(data) {
	if(data.length === 0) {
	  alert("No analyses of data found");
	  return;
	};
	var last = data[data.length - 1];
	$.ajax({
	  url: '/' + config.dataset + '/sources/' + last.id + '/analysis.json',
	  dataType: 'json',
	  success: gotAnalysis
	});
  };

  $.ajax({
	url: '/' + config.dataset + '/sources.json',
	dataType: 'json',
	success: gotSources
  });
};
