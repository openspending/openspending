FROM gliderlabs/alpine:latest

RUN apk add --update python3 py-pip
RUN apk add git
RUN pip install gunicorn
RUN pip install python-memcached
RUN git clone http://github.com/openspending/os-conductor.git app
RUN cd app && pip install -r requirements.txt
RUN rm -rf /var/cache/apk/*

ENV OS_CONDUCTOR_CACHE=cache:11211
ENV OS_API=os-api:8000
ENV OS_CONDUCTOR=os-conductor:8000

EXPOSE 8000

CMD cd app && gunicorn -w 4 conductor.server:app -b 0.0.0.0:8000
