FROM gliderlabs/alpine:3.4

RUN apk add --update python3 git libpq nodejs
RUN apk add --update --virtual=build-dependencies wget libffi libffi-dev ca-certificates python3-dev  build-base
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN cd $(npm root -g)/npm \
 && npm install fs-extra \
 && sed -i -e s/graceful-fs/fs-extra/ -e s/fs\.rename/fs.move/ ./lib/utils/rename.js
RUN npm install npm@latest -g
RUN npm install -g os-types
RUN python3 --version
RUN pip3 --version
RUN pip3 install --upgrade pip
RUN pip3 install os-gobble \
                 celery \
                 git+git://github.com/frictionlessdata/datapackage-pipelines.git
RUN git clone http://github.com/openspending/os-data-importers.git /app
RUN mkdir /root/.gobble
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV DATAPIPELINES_REDIS_HOST="redis"
ENV CELERY_BROKER="amqp://guest:guest@mq:5672//"
ENV CELERY_BACKEND="amqp://guest:guest@mq:5672//"
ENV GIT_REPO=http://github.com/openspending/os-data-importers.git

ADD startup.sh /startup.sh

EXPOSE 5000

CMD /startup.sh
