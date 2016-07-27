FROM gliderlabs/alpine:3.4

RUN apk add --update python3 git libpq
RUN apk add --update --virtual=build-dependencies wget ca-certificates python3-dev build-base
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN pip3 install flower
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV FLOWER_BASIC_AUTH=openspending:rocks

EXPOSE 80

CMD celery flower --address=0.0.0.0 --port=80 --broker=amqp://guest:guest@mq:5672// --broker-api=http://guest:guest@mq:15672/api/ --url_prefix=status/tasks


