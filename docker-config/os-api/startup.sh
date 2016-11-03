#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`
echo OS-API DB: $OS_API_ENGINE

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    pip install -U -r requirements.txt
    pip install -U -e .
else
    (cd /repos/babbage.fiscal-data-package && pip3 install -U -e . && echo using `pwd` dev version) || true
    (cd /repos/babbage && pip3 install -U -e . && echo using `pwd` dev version) || true
    (cd /repos/datapackage-py && pip3 install -U -e . && echo using `pwd` dev version) || true
    (cd /repos/tabulator-py && pip3 install -U -e . && echo using `pwd` dev version) || true
    (cd /repos/jsontableschema-py && pip3 install -U -e . && echo using `pwd` dev version) || true
    (cd /repos/jsontableschema-sql-py && pip3 install -U -e . && echo using `pwd` dev version) || true
fi

FISCAL_PACKAGE_ENGINE=$OS_API_ENGINE bb-fdp-cli create-tables && echo "CREATED TABLES"

python3 --version
python3 -m celery -A babbage_fiscal.tasks --concurrency=4 worker &
gunicorn -t 90 -w 4 os_api.app:app -b 0.0.0.0:8000
