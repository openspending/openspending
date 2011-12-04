(function() {
  var DEFAULT_MAPPING, DIMENSION_TYPE_META, Delegator, DimensionWidget, DimensionsWidget, FIELDS_META, ModelEditor, Widget, util,
    __slice = Array.prototype.slice,
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  $.plugin = function(name, object) {
    return jQuery.fn[name] = function(options) {
      var args;
      args = Array.prototype.slice.call(arguments, 1);
      return this.each(function() {
        var instance;
        instance = $.data(this, name);
        if (instance) {
          return options && instance[options].apply(instance, args);
        } else {
          instance = new object(this, options);
          return $.data(this, name, instance);
        }
      });
    };
  };

  $.a2o = function(ary) {
    var obj, walk;
    obj = {};
    walk = function(o, path, value) {
      var key;
      key = path[0];
      if (path.length === 2 && path[1] === '') {
        if ($.type(o[key]) !== 'array') o[key] = [];
        return o[key].push(value);
      } else if (path.length === 1) {
        return o[key] = value;
      } else {
        if ($.type(o[key]) !== 'object') o[key] = {};
        return walk(o[key], path.slice(1), value);
      }
    };
    $.each(ary, function() {
      var p, path;
      path = this.name.split('[');
      path = [path[0]].concat(__slice.call((function() {
          var _i, _len, _ref, _results;
          _ref = path.slice(1);
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push(p.slice(0, -1));
          }
          return _results;
        })()));
      return walk(obj, path, this.value);
    });
    return obj;
  };

  $.fn.serializeObject = function() {
    var ary;
    ary = this.serializeArray();
    return $.a2o(ary);
  };

  Delegator = (function() {

    Delegator.prototype.events = {};

    Delegator.prototype.options = {};

    Delegator.prototype.element = null;

    function Delegator(element, options) {
      this.options = $.extend(true, {}, this.options, options);
      this.element = $(element);
      this.on = this.subscribe;
      this.addEvents();
    }

    Delegator.prototype.addEvents = function() {
      var event, functionName, sel, selector, _i, _ref, _ref2, _results;
      _ref = this.events;
      _results = [];
      for (sel in _ref) {
        functionName = _ref[sel];
        _ref2 = sel.split(' '), selector = 2 <= _ref2.length ? __slice.call(_ref2, 0, _i = _ref2.length - 1) : (_i = 0, []), event = _ref2[_i++];
        _results.push(this.addEvent(selector.join(' '), event, functionName));
      }
      return _results;
    };

    Delegator.prototype.addEvent = function(bindTo, event, functionName) {
      var closure, isBlankSelector,
        _this = this;
      closure = function() {
        return _this[functionName].apply(_this, arguments);
      };
      isBlankSelector = typeof bindTo === 'string' && bindTo.replace(/\s+/g, '') === '';
      if (isBlankSelector) bindTo = this.element;
      if (typeof bindTo === 'string') {
        this.element.delegate(bindTo, event, closure);
      } else {
        if (this.isCustomEvent(event)) {
          this.subscribe(event, closure);
        } else {
          $(bindTo).bind(event, closure);
        }
      }
      return this;
    };

    Delegator.prototype.isCustomEvent = function(event) {
      var natives;
      natives = "blur focus focusin focusout load resize scroll unload click dblclick\nmousedown mouseup mousemove mouseover mouseout mouseenter mouseleave\nchange select submit keydown keypress keyup error".split(/[^a-z]+/);
      event = event.split('.')[0];
      return $.inArray(event, natives) === -1;
    };

    Delegator.prototype.publish = function() {
      this.element.triggerHandler.apply(this.element, arguments);
      return this;
    };

    Delegator.prototype.subscribe = function(event, callback) {
      var closure;
      closure = function() {
        return callback.apply(this, [].slice.call(arguments, 1));
      };
      closure.guid = callback.guid = ($.guid += 1);
      this.element.bind(event, closure);
      return this;
    };

    Delegator.prototype.unsubscribe = function() {
      this.element.unbind.apply(this.element, arguments);
      return this;
    };

    return Delegator;

  })();

  DEFAULT_MAPPING = {
    amount: {
      type: 'measure',
      datatype: 'float',
      label: 'Amount'
    },
    time: {
      type: 'date',
      datatype: 'date',
      label: 'Time'
    }
  };

  DIMENSION_TYPE_META = {
    date: {
      fixedDataType: true,
      helpText: 'The time dimension represents the time or period over which the\nspending occurred. Please choose the column of your dataset which\ncontains an ISO8601 formatted date (YYYY, YYYY-MM, YYYY-MM-DD, etc.).'
    },
    measure: {
      fixedDataType: true,
      helpText: 'The most important field in the dataset. Please choose which of\nthe columns in your dataset represents the value of the spending,\nand how you\'d like it to be displayed.'
    }
  };

  FIELDS_META = {
    label: {
      required: true
    },
    name: {
      required: true
    }
  };

  util = {
    flattenObject: function(obj) {
      var flat, pathStr, walk;
      flat = {};
      pathStr = function(path) {
        var ary, p;
        ary = [path[0]];
        ary = ary.concat((function() {
          var _i, _len, _ref, _results;
          _ref = path.slice(1);
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push("[" + p + "]");
          }
          return _results;
        })());
        return ary.join('');
      };
      walk = function(path, o) {
        var key, newpath, value, _results;
        _results = [];
        for (key in o) {
          value = o[key];
          newpath = $.extend([], path);
          newpath.push(key);
          if ($.type(value) === 'object') {
            _results.push(walk(newpath, value));
          } else {
            if ($.type(value) === 'array') newpath.push('');
            _results.push(flat[pathStr(newpath)] = value);
          }
        }
        return _results;
      };
      walk([], obj);
      return flat;
    },
    compoundType: function(type) {
      return $.inArray(type, ['attribute', 'value', 'date', 'measure']) === -1;
    }
  };

  Widget = (function() {

    __extends(Widget, Delegator);

    function Widget() {
      Widget.__super__.constructor.apply(this, arguments);
    }

    Widget.prototype.deserialize = function(data) {};

    return Widget;

  })();

  DimensionWidget = (function() {

    __extends(DimensionWidget, Widget);

    DimensionWidget.prototype.events = {
      '.add_field click': 'onAddFieldClick',
      '.field_rm click': 'onFieldRemoveClick'
    };

    function DimensionWidget(name, container, options) {
      this.formFieldRequired = __bind(this.formFieldRequired, this);
      this.formFieldPrefix = __bind(this.formFieldPrefix, this);
      var el;
      this.name = name;
      el = $("<fieldset class='dimension' data-dimension-name='" + this.name + "'>            </fieldset>").appendTo(container);
      DimensionWidget.__super__.constructor.call(this, el, options);
      this.id = "" + (this.element.parents('.modeleditor').attr('id')) + "_dim_" + this.name;
      this.element.attr('id', this.id);
    }

    DimensionWidget.prototype.deserialize = function(data) {
      var formObj, k, v, _ref, _results;
      this.data = (data != null ? data[this.name] : void 0) || {};
      this.meta = DIMENSION_TYPE_META[this.data['type']] || {};
      if (util.compoundType(data.type) && !('fields' in this.data)) {
        this.data.fields = {
          'name': {
            'datatype': 'id'
          },
          'label': {
            'datatype': 'string'
          }
        };
      }
      this.element.html($.tmpl('tpl_dimension', this));
      this.element.trigger('fillColumnsRequest', [this.element.find('select.column')]);
      formObj = {};
      formObj[this.name] = this.data;
      _ref = util.flattenObject(formObj);
      _results = [];
      for (k in _ref) {
        v = _ref[k];
        _results.push(this.element.find("[name=\"" + k + "\"]").val(v));
      }
      return _results;
    };

    DimensionWidget.prototype.formFieldPrefix = function(fieldName) {
      return "" + this.name + "[fields][" + fieldName + "]";
    };

    DimensionWidget.prototype.formFieldRequired = function(fieldName) {
      var _ref;
      return ((_ref = FIELDS_META[fieldName]) != null ? _ref['required'] : void 0) || false;
    };

    DimensionWidget.prototype.onAddFieldClick = function(e) {
      var name, row;
      name = prompt("Field name:").trim();
      row = this._makeFieldRow(name);
      row.appendTo(this.element.find('tbody'));
      this.element.trigger('fillColumnsRequest', [row.find('select.column')]);
      return false;
    };

    DimensionWidget.prototype.onFieldRemoveClick = function(e) {
      $(e.currentTarget).parents('tr').first().remove();
      this.element.parents('form').first().change();
      return false;
    };

    DimensionWidget.prototype._makeFieldRow = function(name, constant) {
      if (constant == null) constant = false;
      return $.tmpl('tpl_dimension_field', {
        'fieldName': name,
        'prefix': this.formFieldPrefix,
        'required': this.formFieldRequired
      });
    };

    return DimensionWidget;

  })();

  DimensionsWidget = (function() {

    __extends(DimensionsWidget, Delegator);

    DimensionsWidget.prototype.events = {
      '.add_attribute_dimension click': 'onAddAttributeDimensionClick',
      '.add_compound_dimension click': 'onAddCompoundDimensionClick',
      '.add_date_dimension click': 'onAddDateDimensionClick',
      '.add_measure click': 'onAddMeasureClick'
    };

    function DimensionsWidget(element, options) {
      DimensionsWidget.__super__.constructor.apply(this, arguments);
      this.widgets = [];
      this.dimsEl = this.element.find('.dimensions').get(0);
    }

    DimensionsWidget.prototype.addDimension = function(name) {
      var w;
      w = new DimensionWidget(name, this.dimsEl);
      this.widgets.push(w);
      return w;
    };

    DimensionsWidget.prototype.removeDimension = function(name) {
      var idx, w, _i, _len, _ref;
      idx = null;
      _ref = this.widgets;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        w = _ref[_i];
        if (w.name === name) {
          idx = this.widgets.indexOf(w);
          break;
        }
      }
      if (idx !== null) return this.widgets.splice(idx, 1)[0].element.remove();
    };

    DimensionsWidget.prototype.deserialize = function(data) {
      var dims, name, obj, toRemove, widget, _i, _j, _len, _len2, _ref, _results;
      if (this.ignoreParent) return;
      dims = data || {};
      toRemove = [];
      _ref = this.widgets;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        widget = _ref[_i];
        if (widget.name in dims) {
          widget.deserialize(data);
          delete dims[widget.name];
        } else {
          toRemove.push(widget.name);
        }
      }
      for (_j = 0, _len2 = toRemove.length; _j < _len2; _j++) {
        name = toRemove[_j];
        this.removeDimension(name);
      }
      _results = [];
      for (name in dims) {
        obj = dims[name];
        _results.push(this.addDimension(name).deserialize(data));
      }
      return _results;
    };

    DimensionsWidget.prototype.promptAddDimension = function(props) {
      var data, name;
      name = prompt("Dimension name:");
      if (!name) return false;
      data = {};
      data[name] = props;
      return this.addDimension(name.trim()).deserialize(data);
    };

    DimensionsWidget.prototype.onAddAttributeDimensionClick = function(e) {
      this.promptAddDimension({
        'type': 'attribute'
      });
      return false;
    };

    DimensionsWidget.prototype.onAddCompoundDimensionClick = function(e) {
      this.promptAddDimension({
        'type': 'compound'
      });
      return false;
    };

    DimensionsWidget.prototype.onAddDateDimensionClick = function(e) {
      this.promptAddDimension({
        'type': 'date',
        'datatype': 'date'
      });
      return false;
    };

    DimensionsWidget.prototype.onAddMeasureClick = function(e) {
      this.promptAddDimension({
        'type': 'measure',
        'datatype': 'float'
      });
      return false;
    };

    return DimensionsWidget;

  })();

  ModelEditor = (function() {

    __extends(ModelEditor, Delegator);

    ModelEditor.prototype.widgetTypes = {
      '.dimensions_widget': DimensionsWidget
    };

    ModelEditor.prototype.events = {
      'modelChange': 'onModelChange',
      'fillColumnsRequest': 'onFillColumnsRequest',
      '.forms form submit': 'onFormSubmit',
      '.forms form change': 'onFormChange'
    };

    function ModelEditor(element, options) {
      var ctor, e, selector, _i, _len, _ref, _ref2;
      ModelEditor.__super__.constructor.apply(this, arguments);
      this.data = $.extend(true, {}, DEFAULT_MAPPING);
      this.widgets = [];
      this.form = $(element).find('.forms form').eq(0);
      this.id = this.element.attr('id');
      if (!(this.id != null)) {
        this.id = Math.floor(Math.random() * 0xffffffff).toString(16);
        this.element.attr('id', this.id);
      }
      this.element.find('script[type="text/x-jquery-tmpl"]').each(function() {
        return $(this).template($(this).attr('id'));
      });
      this.element.find('select.column').each(function() {
        return $(this).trigger('fillColumnsRequest', [this]);
      });
      _ref = this.widgetTypes;
      for (selector in _ref) {
        ctor = _ref[selector];
        _ref2 = this.element.find(selector).get();
        for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
          e = _ref2[_i];
          this.widgets.push(new ctor(e));
        }
      }
      this.element.trigger('modelChange');
    }

    ModelEditor.prototype.onFormChange = function(e) {
      if (this.ignoreFormChange) return;
      this.data = this.form.serializeObject();
      this.ignoreFormChange = true;
      this.element.trigger('modelChange');
      return this.ignoreFormChange = false;
    };

    ModelEditor.prototype.onFormSubmit = function(e) {
      return false;
    };

    ModelEditor.prototype.onModelChange = function() {
      var k, v, w, _i, _len, _ref, _ref2;
      _ref = util.flattenObject(this.data);
      for (k in _ref) {
        v = _ref[k];
        this.form.find("[name=\"" + k + "\"]").val(v);
      }
      _ref2 = this.widgets;
      for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
        w = _ref2[_i];
        w.deserialize($.extend(true, {}, this.data));
      }
	  var payload = JSON.stringify(this.data, null, 2);
	  return this.updateEditor(payload);
    };

    ModelEditor.prototype.onFillColumnsRequest = function(elem) {
      var x;
      return $(elem).html(((function() {
        var _i, _len, _ref, _results;
        _ref = this.options.columns;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          _results.push("<option name='" + x + "'>" + x + "</option>");
        }
        return _results;
      }).call(this)).join('\n'));
    };

	ModelEditor.prototype.updateEditor = function(data) {
	  var getEditor = this.options.getEditor || function() {
		return top.document.getEditor();
	  };
	  return getEditor().getSession().setValue(data);
	};

    return ModelEditor;

  })();

  $.plugin('modelEditor', ModelEditor);

  this.ModelEditor = ModelEditor;

}).call(this);
