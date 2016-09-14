#!/bin/sh
set -e

while ! ping -c1 redis &>/dev/null; do :; done && echo "REDIS is UP"
while ! ping -c1 mq &>/dev/null; do :; done && echo "MQ is UP"

(ls $WORKDIR/.git > /dev/null && cd $WORKDIR) || cd /app
echo working from `pwd`

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
else
    (ls $WORKDIR/.git > /dev/null && cd $WORKDIR) && cd /repos/os-data-importers
fi

rm celerybeat-schedule || ls -la
pwd
pip3 install -U git+git://github.com/frictionlessdata/datapackage-pipelines.git
celery -b amqp://guest:guest@mq:5672// --concurrency=4 -B -A datapackage_pipelines.app -Q datapackage-pipelines worker &
dpp serve
