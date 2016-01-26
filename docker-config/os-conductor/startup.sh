#!/bin/sh
set -e

python3 --version

( cd /repos/os-conductor && pip install -r requirements.txt) || true

gunicorn -w 1 conductor.server:app -b 0.0.0.0:8000
