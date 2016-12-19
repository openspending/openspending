#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    cd /remote && npm install && node_modules/.bin/gulp
else
    ( cd /repos/os-explorer && npm install && node_modules/.bin/gulp  ) || true
fi

rm /www || true
ln -s `pwd` /www
chmod a+rwx /www
ls -la /www/

echo "{\"baseUrl\":\"\", \"snippets\": {\"ga\": \"$OS_SNIPPETS_GA\"}}" > /www/config.json

nginx
