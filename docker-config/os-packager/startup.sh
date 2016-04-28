#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

( cd /repos/os-packager && npm install && node_modules/.bin/gulp  ) || true
( cd /repos/os-packager && node_modules/.bin/gulp watch & ) || true

npm start
