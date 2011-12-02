(function ($) {
  $(document).ready(function () {
    var isDatasetNew = $('.container .dataset.new').length > 0;
    if (isDatasetNew) {
      var $datasetInfo = $('.dataset-info');
      var $importOptions = $('.import-options');
      // first the simpler one: the non-Datahub option
      // (just show the hidden form)
      $('.import-options .import-nondatahub a.btn').click(function(e) {
        $importOptions.hide();
        $datasetInfo.show();
      });
      $('.import-datahub form').submit(function(e) {
        e.preventDefault();
        var $form = $(e.target);
        $form.find('input[type="submit"]').val('Loading, please wait ...');
        var datahubUrl = $form.find('input[name="datahubUrl"]').val();
        var regex = /(https?):\/\/(.*)\/dataset\/([^\/]+)$/;
        var parts = datahubUrl.match(regex);
        if (parts === null) {
          msg = 'The DataHub url provided is invalid: ' + datahubUrl + ' Please check it and try again';
          alert(msg);
        }
        var jsonUrl = parts[1] + '://' + parts[2] + '/api/rest/dataset/' + parts[3];
        $.ajax({
          url: jsonUrl,
          dataType: 'jsonp',
          success: function(data) {
            $datasetInfo.find('form input[name="label"]').val(data.title);
            $datasetInfo.find('form input[name="name"]').val(data.name);
            $datasetInfo.find('form textarea[name="description"]').val(data.notes);
            $importOptions.hide();
            $datasetInfo.show();
          },
          // unfortunately pointless as we are doing jsonp!
          error: function(e) {
            alert('Failed to retrieve data from: ' + jsonUrl);
          }
        })
      });
    }
  });
}(jQuery));
