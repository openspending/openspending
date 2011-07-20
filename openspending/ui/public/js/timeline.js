
$(function(){
    var minYear = Number.MAX_VALUE, 
        maxYear = Number.MIN_VALUE,
        maxValue = Number.MIN_VALUE,
        minValue = Number.MAX_VALUE,
        sum = [],
        i, j;
    for (i=0; i<data.length; i+=1){
        for (j=0; j<data[i].length; j+=1){
            data[i][j].x = parseInt(data[i][j].x, 10);
            minYear = Math.min(minYear, data[i][j].x);
            maxYear = Math.max(maxYear, data[i][j].x);
            data[i][j].y = Math.abs(data[i][j].y);
            sum[j] = sum[j] || 0;
            sum[j] += data[i][j].y;
        }
    }
    for (i=0; i<sum.length; i++){
        maxValue = Math.max(maxValue, sum[i]);
        minValue = Math.min(minValue, sum[i]);
    }

    
    minValue = 0;
    /* Sizing and scales. */
    var l = 10 + String(maxValue).length * 10,
        w = 950 - l - 10,
        h = 400,
        x = pv.Scale.linear(minYear, maxYear).range(0, w),
        y = pv.Scale.linear(minValue, maxValue).range(0, h),
        currentYear = 0,
        currentFunction = 0
        ;

    /* The root panel. */
    var vis = new pv.Panel()
        .width(w)
        .height(h)
        .bottom(20)
        .left(l)
        .right(10)
        .top(5)
        .canvas("vis");

    /* X-axis and ticks. */
    vis.add(pv.Rule)
        .data(x.ticks())
        .visible(function(d) {
            return d;
        })
        .left(x)
        .bottom(-5)
        .height(5)
        .anchor("bottom").add(pv.Label)
            .text(function(d){
                return x.tickFormat(d).replace(/,/, "");
            });

        /* The stack layout. */
    var layout = vis.add(pv.Layout.Stack)
            .layers(data)
            .x(function(d) {
                return x(d.x);
            })
            .y(function(d) {
                return y(d.y);
            })
            .order("inside-out")
          // .offset("wiggle")
        ;
    var area = layout.layer.add(pv.Area)
        .events("all")
        .interpolate("cardinal")
        .title(function(d){
            return meta[d.meta].label + ": " + currentYear;
        })
        .cursor("pointer")
        .event("mouseover", function(d) {
            d.color = this.fillStyle();
            currentFunction = d.meta;
            var mx = x.invert(vis.mouse().x);
            var i = pv.search(data[0].map(function(d) {
                return d.x;
            }), mx);
            currentYear = i < 0 ? (-i - 2) : i;
            window.setTimeout(function(){
                vis.render();
            },0);
            console.log("CurrentYear: ", currentYear, "Current Function: ", currentFunction);
            return this.fillStyle(this.fillStyle().alpha(0.75));
        })
        .event("mouseout", function(d) {
            currentFunction = -1;
            currentYear = -1;
            this.fillStyle(d.color);
            return this;
        })
        .event("click", function(d) {
            document.location.href = "/classifier/" + meta[d.meta].taxonomy + "/" + meta[d.meta].name;
        });

    var dot = layout.add(pv.Dot)
        .visible(function(a, d) {
            console.log(this, arguments);
            console.log("Dot visible? ", currentYear >= 0 && currentFunction >= 0);
            return true;
            // return currentYear >= 0 && currentFunction >= 0;
        })
        .left(function(d) {
            console.log(this, arguments, x(data[currentFunction][currentYear].x));
            return x(data[currentFunction][currentYear].x);
        })
        .bottom(function(d) {
            return y(data[currentFunction][currentYear].y);
        })
        .fillStyle(function() {
            return area.fillStyle();
        })
        .strokeStyle("#000")
        .size(20) 
        .lineWidth(1)
        .anchor("right").add(pv.Label)
            .text(function(d) {
                return "label";
            });

    /* Y-axis and ticks. */
    vis.add(pv.Rule)
        .data(y.ticks(3))
        .bottom(y)
        .strokeStyle(function(d) {
            return d ? "rgba(128,128,128,.2)" : "#000";
        })
        .anchor("left").add(pv.Label)
            .text(function(d){
              return y.tickFormat(d) + " " + currency;
            });

    // vis.add(pv.Bar)
    //     .fillStyle("rgba(0,0,0,.001)")
    //     .event("mouseout", function(){
    //         currentYear = -1;
    //         return vis;
    //     })
    //     .event("mousemove", function(){
    //         var mx = x.invert(vis.mouse().x);
    //         var i = pv.search(data[0].map(function(d) {
    //             return d.x;
    //         }), mx);
    //         currentYear = i < 0 ? (-i - 2) : i;
    //         return vis;
    //     });

    vis.render();
});
