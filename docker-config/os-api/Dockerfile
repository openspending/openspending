FROM gliderlabs/alpine:3.3

RUN apk add --update python3 git libpq
RUN apk add --update --virtual=build-dependencies wget ca-certificates python3-dev postgresql-dev build-base
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN pip3 install psycopg2
RUN pip3 install --upgrade pip
RUN pip3 install gunicorn
RUN pip3 install python-memcached
RUN pip3 install git+git://github.com/openspending/babbage.fiscal-data-package.git
RUN pip3 install -U git+git://github.com/openspending/babbage.git
RUN pip3 install -U git+git://github.com/akariv/tabulator-py.git
RUN pip3 install -U git+git://github.com/okfn/datapackage-py.git
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-py.git
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-sql-py.git
RUN git clone http://github.com/openspending/os-api.git app
RUN cd app && pip install -e .
RUN pip3 install git+git://github.com/openspending/babbage.fiscal-data-package.git
RUN pip3 install -U git+git://github.com/openspending/babbage.git
RUN pip3 install -U git+git://github.com/okfn/datapackage-py.git
RUN pip3 install -U git+git://github.com/akariv/tabulator-py.git
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-py.git
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-sql-py.git
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV OS_API_CACHE=cache:11211
ENV CELERY_CONFIG=amqp://guest:guest@mq:5672//
ENV CELERY_BACKEND_CONFIG=amqp://guest:guest@mq:5672//

ADD startup.sh /startup.sh

EXPOSE 8000

CMD  /startup.sh
