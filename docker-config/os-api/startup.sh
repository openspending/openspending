#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`
echo OS-API DB: $OS_API_ENGINE

(cd /repos/babbage.fiscal-data-package && pip3 install -U -e . && echo using `pwd` dev version) || true
(cd /repos/babbage && pip3 install -U -e . && echo using `pwd` dev version) || true
(cd /repos/datapackage-py && pip3 install -U -e . && echo using `pwd` dev version) || true
(cd /repos/tabulator-py && pip3 install -U -e . && echo using `pwd` dev version) || true
(cd /repos/jsontableschema-py && pip3 install -U -e . && echo using `pwd` dev version) || true
(cd /repos/jsontableschema-sql-py && pip3 install -U -e . && echo using `pwd` dev version) || true

FISCAL_PACKAGE_ENGINE=$OS_API_ENGINE bb-fdp-cli create-tables && echo "CREATED TABLES"

python3 --version
python3 -m celery -A babbage_fiscal.tasks --concurrency=1 worker &
gunicorn -w 4 os_api.app:app -b 0.0.0.0:8000
