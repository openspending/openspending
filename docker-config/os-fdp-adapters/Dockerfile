FROM gliderlabs/alpine:3.4

RUN apk add --update python3 git libpq
RUN apk add --update --virtual=build-dependencies wget ca-certificates python3-dev build-base libxml2-dev libxslt-dev
RUN update-ca-certificates
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN git clone http://github.com/openspending/os-fdp-adapters.git app
RUN cd app && pip3 install -r requirements.txt
RUN pip3 install gunicorn
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ADD startup.sh /startup.sh

EXPOSE 8000

CMD  /startup.sh
