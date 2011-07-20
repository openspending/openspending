/* Author: 

*/
/*global countries: true, stats: true, $: true */

$(function(){
    $(".flag-box").each(function(index, elem){
        var form = $($(elem).find("form.flag-form"));
        form.find("input[type='submit']").hide();
        form.find("input").change(function(){
            $.post(form.attr("action"), $(this).serialize());
            var el = $(this);
            var flag = el.val();
            var label = el.parent();
            var text = label.text();
            var value = parseInt(label.attr("data-flagcount"), 10);
            text = text.replace(/(.*)\(\d+\)/, "$1("+(value+1)+")");
            label.parent().after('<li data-flagcount="'+value+'">'+text+'</li>');
            label.parent().hide();
        });
    });

    $("#show-search-help-text").click(function(e) {
      $(".search-help-text").slideToggle();
    });
});


var makeChloroplethMap = function(elementId, width, height, data, mouseover, mouseout, clickfunc){
    var fill = pv.Scale.linear(0, 100)
        .range("#0ff", "#00f");
    
    /* Precompute the country's population density and color. */
    countries.forEach(function(c) {
      c.transparencyRanking = data[c.code.toLowerCase()];
      c.color = data[c.code.toLowerCase()] ? fill(data[c.code.toLowerCase()]) : "#eee"; // unknown
      c.currentColor = c.color;
    });

    var w = width,
        h = 3 / 5 * w;
    // h = height;
    var geo = pv.Geo.scale("none").range(w - 20, h);

    var vis = new pv.Panel()
        .canvas(elementId)
        .width(w)
        .height(h)
        .fillStyle("#fff");

    /* Countries. */
    vis.add(pv.Panel)
        .data(countries)
      .add(pv.Panel)
        .data(function(c) {return c.borders;})
      .add(pv.Line)
        .data(function(b) {return b;})
        .left(geo.x)
        .top(geo.y)
        .cursor(function(d,b,c){
            if (c.transparencyRanking){
                return "pointer";
            }
        })
        .title(function(d, b, c) {return c.name;})
        .event("mouseover", function(d, b, c) {
            if (c.transparencyRanking){
                mouseover(c);
                c.currentColor = "#000";
            }
            return vis;
        })
        .event("mouseout", function(d, b, c) {
            if (c.transparencyRanking){
                mouseout(c);
                c.currentColor = c.color;
            }
            return vis;
        })
        .event("click", function(d, b, c) {
            if (c.transparencyRanking){
                clickfunc(c);
            }
            return vis;
        })
        .fillStyle(function(d, b, c) {return c.currentColor;})
        .strokeStyle(function() {return this.fillStyle().darker();})
       .lineWidth(1)
        .antialias(true);

    vis.render();

};


















