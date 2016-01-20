(cd /repos/babbage && pip install -U -e . && echo using `pwd` dev version) || true
(cd /repos/babbage.fiscal-data-package && pip install -U -e . && echo using `pwd` dev version) || true
(cd /repos/tabulator-py && pip install -U -e . && echo using `pwd` dev version) || true
(cd /repos/datapackage-py && pip install -U -e . && echo using `pwd` dev version) || true
python -m celery -A babbage_fiscal.tasks worker &
gunicorn -w 4 os_api.app:app -b 0.0.0.0:8000
