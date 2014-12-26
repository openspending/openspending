from flask.ext.assets import Bundle

from openspending.core import assets


# Javscript bundles

js = Bundle('js/json2.js',
            filters='jsmin', output='prod/packed.js')
assets.register('js_all', js)


# CSS / Stylesheet bundles

css_main = Bundle('style/bootstrap.css',
                  'style/pygments.css',
                  'style/style.css',
                  filters='cssmin',
                  output='prod/main.css')

assets.register('css_main', css_main)
