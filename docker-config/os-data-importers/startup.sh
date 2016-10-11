#!/bin/sh
set -e

while ! ping -c1 redis &>/dev/null; do :; done && echo "REDIS is UP"
while ! ping -c1 mq &>/dev/null; do :; done && echo "MQ is UP"

(ls $WORKDIR/.git > /dev/null && cd $WORKDIR) || cd /app
echo working from `pwd`

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && 
	git clone $GIT_REPO /remote && 
	cd /remote &&
	git clone http://github.com/os-data/eu-structural-funds.git;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
else
    (ls $WORKDIR/.git > /dev/null && cd $WORKDIR) && cd /repos/os-data-importers
fi

npm install -g os-types
rm celerybeat-schedule || ls -la
pwd
pip3 install -U git+git://github.com/frictionlessdata/datapackage-pipelines.git
pip3 install -U git+git://github.com/openspending/datapackage-pipelines-fiscal.git
dpp init
cd eu-structural-funds
export PYTHONPATH=$PYTHONPATH:`pwd`
export DATAPIPELINES_PROCESSOR_PATH=`pwd`/common/processors
pip3 install -r requirements.txt
python3 -m common.bootstrap update
cd ..
dpp
python3 -m celery -b amqp://guest:guest@mq:5672// --concurrency=4 -B -A datapackage_pipelines.app -Q datapackage-pipelines -l INFO worker &
dpp serve
