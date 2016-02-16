#!/bin/sh
set -e

( cd /repos/os-viewer && npm install ) || true
( cd /repos/os-viewer && node node_modules/gulp/bin/gulp.js ) || true

npm start
