FROM gliderlabs/alpine:3.4

RUN apk add --update python3 git libpq wget ca-certificates python3-dev postgresql-dev build-base \
                     libxml2-dev libxslt-dev libstdc++
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN pip3 install --upgrade pip
RUN git clone http://github.com/openspending/os-api.git app
RUN cd app && pip install -r requirements.txt
RUN rm -rf /var/cache/apk/*

ENV OS_API_CACHE=cache:11211
ENV OS_STATSD_HOST=10.7.255.254
ENV CELERY_CONFIG=amqp://guest:guest@mq:5672//
ENV CELERY_BACKEND_CONFIG=amqp://guest:guest@mq:5672//

ADD startup.sh /startup.sh

EXPOSE 8000

CMD  /startup.sh
