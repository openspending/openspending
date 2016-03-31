#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

( cd /repos/os-viewer && npm install ) || true
( cd /repos/os-viewer && node node_modules/gulp/bin/gulp.js ) || true

npm start
