from flask.ext.assets import Bundle

from openspending.core import assets


# Javscript bundles

js_base = Bundle('vendor/jquery/dist/jquery.js',
                 'vendor/jquery.cookie/jquery.cookie.js',
                 'vendor/chosen_v1.3.0/chosen.jquery.js',
                 'vendor/bootstrap/dist/js/bootstrap.js',
                 'vendor/typeahead.js/dist/typeahead.jquery.js',
                 'vendor/yepnope/dist/yepnope-2.0.0.js',
                 'vendor/base64/base64.js',
                 'vendor/accounting/accounting.js',
                 'vendor/underscore/underscore.js',
                 'vendor/handlebars/handlebars.js',
                 'openspendingjs/lib/boot.js',
                 'openspendingjs/lib/utils/utils.js',
                 'openspendingjs/lib/aggregator.js',
                 filters='uglifyjs', output='prod/base.js')
assets.register('js_base', js_base)


# CSS / Stylesheet bundles

css_main = Bundle('style/base.less',
                  'style/pygments.css',
                  'style/bs2_style.less',
                  'style/views.less',
                  'style/dimensions.less',
                  filters='less,cssmin',
                  output='prod/main.css')

assets.register('css_main', css_main)

css_embed = Bundle(css_main,
                   'style/embed.less',
                   filters='less,cssmin',
                   output='prod/embed.css')

assets.register('css_embed', css_embed)
