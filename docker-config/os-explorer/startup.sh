#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    cd /remote && npm install && npm run build
else
    ( cd /repos/os-explorer && npm install && npm run build  ) || true
fi

echo "{\"baseUrl\":\"\", \"snippets\": {\"ga\": \"$OS_SNIPPETS_GA\"}}" > config.json

ls -la
find public
node server.js
