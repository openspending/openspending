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
    cat config.js | sed s/next.openspending.org/staging.openspending.org/ > config.js.tmp
    mv -f config.js.tmp config.js
else
    ( cd /repos/os-admin && npm install && npm run build  &&
      cat config.js | sed s/next.openspending.org/dev.openspending.org/ > config.js.tmp &&
      mv -f config.js.tmp config.js
    ) || true
fi


#cat config.js | sed "s/ga: null/ga: \"$OS_SNIPPETS_GA\"/" > config.js.tmp &&
#      mv -f config.js.tmp config.js

rm /www || true
ln -s `pwd` /www
chmod a+rwx /www
ls -la /www/

nginx
