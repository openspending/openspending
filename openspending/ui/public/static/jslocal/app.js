(function ($) {
  $(document).ready(function () {
    var isDatasetNew = $('.container .dataset.new').length > 0;
    if (isDatasetNew) {
      setupImportOptions();
    }
    // setup source dropdown if we have CKAN-URI
    setupNewSource($('#new-source'));

    setupLocales();
    setupDatasetListing();
  });

function getCkanDatasetInfo(datasetUrl) {
  var regex = /(https?):\/\/(.*)\/dataset\/([^\/]+)$/;
  var parts = datasetUrl.match(regex);
  if (parts === null) {
    msg = 'The DataHub url provided is invalid: ' + datasetUrl + ' Please check it and try again';
    alert(msg);
  }
  var jsonUrl = parts[1] + '://' + parts[2] + '/api/rest/dataset/' + parts[3];
  var jqxhr = $.ajax({
    url: jsonUrl,
    dataType: 'jsonp'
  });
  return jqxhr;
}

function setupImportOptions() {
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
    getCkanDatasetInfo(datahubUrl)
      .then(function(data) {
        $datasetInfo.find('form input[name="label"]').val(data.title);
        $datasetInfo.find('form input[name="name"]').val(data.name);
        $datasetInfo.find('form input[name="ckan_uri"]').val(datahubUrl);
        $datasetInfo.find('form textarea[name="description"]').val(data.notes);
        $importOptions.hide();
        $datasetInfo.show();
      })
      // unfortunately pointless as we are doing jsonp!
      .error(function(e) {
        alert('Failed to retrieve data from: ' + jsonUrl);
      })
  });
}

function setupNewSource($els) {
  $els.each(function(idx, $el) {
    $el = $($el);
    var dataHubUri = $el.attr('ckan-uri');
    if (!dataHubUri) {
      return;
    } else {
      getCkanDatasetInfo(dataHubUri).then(function(data) {
        var $input = $el.find('input[name="url"]');
        $input.hide();
        $input.after($('<select name="url"></select>'));
        var $select = $el.find('select');
        $.each(data.resources, function(idx, resource) {
          var _text = resource.name + ' -- ' + resource.description + ' -- ' + resource.url;
          var _option = $('<option />').val(resource.url).text(_text);
          $select.append(_option);
        });
      });
    }
  });
}

function setupLocales() {
  $('.select-locale').click(function(event) {
      $.ajax({url: '/set-locale',
            data: {locale: $(this).data('locale')},
            type: 'POST',
            async: false,
            });
      window.location.reload();
    });
}

function updateDatasetListing(params) {
  params = params || {};
  var $el = $('#datasets');
  var jqxhr = $.ajax({
    url: '/datasets.json',
    data: params
    })
  jqxhr.then(function(out) {
    var $list = $el.find('.listing').first();
    $list.empty();
    out.hasTerritories = out.territories.length > 1;
    out.territories = _.map(out.territories, function(t) {
      t.selected = t.code == params.territories;
      return t;
    });
    out.hasLanguages = out.languages.length > 1;
    out.languages = _.map(out.languages, function(t) {
      t.selected = t.code == params.languages;
      return t;
    });
    out.datasets = _.map(out.datasets, function(t) {
      t.tagline = t.description.substring(0, 60);
      if (t.description.length > 60) {
        t.tagline += "...";
      }
      return t;
    });
    var template = Handlebars.compile($("#listing-template").html());
    $list.append(template(out));
    $('.filter-datasets').change(function(event) {
      var $t = $(event.target);
      params[$t.attr('name')] = $t.val().length ? $t.val() : undefined;
      updateDatasetListing(params);
    });
    if ($el.is(':hidden')) {
      $el.modal({backdrop: true});
    }
  });
}

window.updateDatasetListing = updateDatasetListing;

function setupDatasetListing() {
  $('.list-datasets').click(function(event) {
    updateDatasetListing();
    return false;
  });

  $('.fp-map svg').click(function(event) {
    console.log(event);
    return false;
  });
}

// end the local closure
}(jQuery));

