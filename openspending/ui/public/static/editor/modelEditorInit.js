
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

  $.ajax({
	url: '/' + config.dataset + '/sources/' + config.source + '/analysis.json',
	dataType: 'json',
	success: gotAnalysis
  });

};
