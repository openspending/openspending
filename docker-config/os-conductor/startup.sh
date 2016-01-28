#!/bin/sh
set -e

python3 --version

( cd /repos/os-conductor && pip install -r requirements.txt) || true

ls -la /secrets
cp -f /secrets/$SECRETS_PATH/* /secrets
ls -la /secrets
gunicorn -w 2 conductor.server:app -b 0.0.0.0:8000
