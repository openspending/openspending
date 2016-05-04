#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

rm /www || true
ln -s `pwd` /www
chmod a+rwx /www
ls -la /www/

echo '{"baseUrl":""}' > /www/config.json

( cd /repos/os-explorer && npm install && node_modules/.bin/gulp  ) || true

nginx
