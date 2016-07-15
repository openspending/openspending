#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`
echo DB: $OS_CONDUCTOR_ENGINE

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    pip install -r requirements.txt
    cat conductor/blueprints/user/lib/lib.js | sed s/next.openspending.org/staging.openspending.org/ > lib.js.tmp
    mv -f lib.js.tmp conductor/blueprints/user/lib/lib.js
else
    ( cd /repos/os-conductor && pip install -r requirements.txt &&
      cat conductor/blueprints/user/lib/lib.js | sed s/next.openspending.org/dev.openspending.org/ > lib.js.tmp &&
      mv -f lib.js.tmp conductor/blueprints/user/lib/lib.js
    ) || true
fi

gunicorn -w 4 conductor.server:app -b 0.0.0.0:8000
