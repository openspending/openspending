#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

ln -fs `pwd` /www
echo '{"baseUrl":""}' > /www/config.json

( cd /repos/os-explorer && npm install && node_modules/.bin/gulp  ) || true

nginx
