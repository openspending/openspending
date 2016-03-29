#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

( cd /repos/os-packager && npm install ) || true
( cd /repos/os-packager && node node_modules/gulp/bin/gulp.js ) || true

npm start
