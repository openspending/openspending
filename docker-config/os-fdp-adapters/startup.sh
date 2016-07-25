#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    pip3 install -r requirements.txt
else
    (cd /repos/os-fdp-adapters && pip3 install -U requirements.txt)
fi

gunicorn -w 4 os_fdp_adapters:wsgi -b 0.0.0.0:8000
