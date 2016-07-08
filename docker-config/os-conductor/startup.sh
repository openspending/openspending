#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`
echo DB: $OS_CONDUCTOR_ENGINE

( cd /repos/os-conductor && pip install -r requirements.txt &&
  cat conductor/blueprints/user/lib/lib.js | sed s/next.openspending.org/dev.openspending.org/ > lib.js.tmp &&
  mv -f lib.js.tmp conductor/blueprints/user/lib/lib.js
) || true

ls -la /secrets
cp -f /secrets/$SECRETS_PATH/* /secrets

gunicorn -w 4 conductor.server:app -b 0.0.0.0:8000
