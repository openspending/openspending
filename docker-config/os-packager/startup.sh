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
    ( cd /repos/os-packager && npm install && node_modules/.bin/gulp  ) || true
    ( cd /repos/os-packager && node_modules/.bin/gulp watch & ) || true
fi


npm start
