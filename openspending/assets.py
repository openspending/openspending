from flask.ext.assets import Bundle

from openspending.core import assets


# Javscript bundles

js = Bundle('js/json2.js',
            filters='jsmin', output='prod/packed.js')
assets.register('js_all', js)


# CSS / Stylesheet bundles

css_main = Bundle('style/base.less',
                  'style/pygments.css',
                  'style/style.css',
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
