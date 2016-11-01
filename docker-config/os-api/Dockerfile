FROM gliderlabs/alpine:3.4

RUN apk add --update python3 git libpq wget ca-certificates python3-dev postgresql-dev build-base \
                     libxml2-dev libxslt-dev libstdc++
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN pip3 install psycopg2
RUN pip3 install --upgrade pip
RUN pip3 install gunicorn cchardet python-memcached awesome-slugify regex
RUN pip3 install git+git://github.com/openspending/babbage.fiscal-data-package.git
RUN pip3 install -U git+git://github.com/openspending/babbage.git@feature/optimize-member-queries
RUN pip3 install -U git+git://github.com/frictionlessdata/tabulator-py.git@v0.10.4
RUN pip3 install -U git+git://github.com/frictionlessdata/datapackage-py.git@v0.8.4
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-py.git@0.6.5
RUN pip3 install -U git+git://github.com/akariv/jsontableschema-sql-py.git@feature/auto-index
RUN git clone http://github.com/openspending/os-api.git app
RUN cd app && pip install -e .
RUN pip3 install git+git://github.com/openspending/babbage.fiscal-data-package.git
RUN pip3 install -U git+git://github.com/openspending/babbage.git@feature/optimize-member-queries
RUN pip3 install -U git+git://github.com/frictionlessdata/datapackage-py.git@v0.8.4
RUN pip3 install -U git+git://github.com/frictionlessdata/tabulator-py.git@v0.10.4
RUN pip3 install -U git+git://github.com/frictionlessdata/jsontableschema-py.git@0.6.5
RUN pip3 install -U git+git://github.com/akariv/jsontableschema-sql-py.git@feature/auto-index
RUN rm -rf /var/cache/apk/*

ENV OS_API_CACHE=cache:11211
ENV CELERY_CONFIG=amqp://guest:guest@mq:5672//
ENV CELERY_BACKEND_CONFIG=amqp://guest:guest@mq:5672//

ADD startup.sh /startup.sh

EXPOSE 8000

CMD  /startup.sh
