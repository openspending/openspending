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
    cat config.json | sed s/next.openspending.org/staging.openspending.org/ > config.json.tmp
    mv -f config.json.tmp config.json
else
    ( cd /repos/os-admin && npm install && npm run build  &&
      cat config.json | sed s/next.openspending.org/dev.openspending.org/ > config.json.tmp &&
      mv -f config.json.tmp config.json
    ) || true
fi

rm /www || true
ln -s `pwd` /www
chmod a+rwx /www
ls -la /www/

nginx
