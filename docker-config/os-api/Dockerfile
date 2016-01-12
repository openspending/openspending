FROM gliderlabs/alpine:latest

RUN apk add --update python3 py-pip
RUN apk add git
RUN apk add py-psycopg2 --update-cache  --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted
RUN python3 --version
RUN pip --version
RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install git+git://github.com/okfn/tabulator-py.git
RUN pip install git+git://github.com/okfn/datapackage-py.git
RUN pip install git+git://github.com/openspending/babbage.fiscal-data-package.git
RUN pip install -U git+git://github.com/openspending/babbage.git@add-group-for-dimensions
RUN git clone http://github.com/openspending/os-api.git app
RUN cd app && ls && pip install -e .
RUN rm -rf /var/cache/apk/*
RUN du -d1 -h /usr/lib/python2.7

EXPOSE 8000

CMD cd app && echo $OS_API_ENGINE && gunicorn -w 4 os_api.app:app -b 0.0.0.0:8000
