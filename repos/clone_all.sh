#!/bin/bash
(cd repos && \
git clone https://github.com/okfn/tabulator-py.git && \
git clone https://github.com/okfn/datapackage-py.git && \
git clone https://github.com/openspending/babbage.fiscal-data-package.git && \
git clone https://github.com/openspending/babbage.git && \
git clone https://github.com/openspending/os-api.git && \
git clone https://github.com/openspending/os-conductor.git && \
git clone https://github.com/openspending/os-packager.git && \
git clone https://github.com/openspending/os-viewer.git && \
cd ..)
