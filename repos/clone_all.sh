#!/bin/bash
(cd repos && \
rm -rf tabulator-py && \
git clone https://github.com/okfn/tabulator-py.git && \
rm -rf datapackage-py && \
git clone https://github.com/okfn/datapackage-py.git && \
rm -rf babbage.fiscal-data-package && \
git clone https://github.com/openspending/babbage.fiscal-data-package.git && \
rm -rf babbage && \
git clone https://github.com/openspending/babbage.git && \
rm -rf os-api && \
git clone https://github.com/openspending/os-api.git && \
rm -rf os-conductor
git clone https://github.com/openspending/os-conductor.git && \
rm -rf os-packager
git clone https://github.com/openspending/os-packager.git && \
rm -rf os-viewer
git clone https://github.com/openspending/os-viewer.git && \
rm -rf jsontableschema-py
git clone https://github.com/frictionlessdata/jsontableschema-py.git && \
rm -rf jsontableschema-sql-py
git clone https://github.com/frictionlessdata/jsontableschema-sql-py.git && \
cd ..)
