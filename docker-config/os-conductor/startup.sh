#!/bin/sh
set -e

python3 --version

( cd /repos/os-conductor && pip install -r requirements.txt &&
  cat conductor/blueprints/authorization/lib/lib.js | sed s/s145.okserver.org/dev.openspending.org/ > lib.js.tmp &&
  mv -f lib.js.tmp conductor/blueprints/authorization/lib/lib.js
) || true

ls -la /secrets
cp -f /secrets/$SECRETS_PATH/* /secrets
ls -la /secrets
gunicorn -w 2 conductor.server:app -b 0.0.0.0:8000
