#!/bin/sh
set -e

( cd /repos/os-packager && npm install ) || true
( cd /repos/os-packager && node node_modules/gulp/bin/gulp.js ) || true

npm start
