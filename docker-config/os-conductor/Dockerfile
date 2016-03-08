FROM gliderlabs/alpine:3.3

RUN apk add --update python3 git libpq
RUN apk add --update --virtual=build-dependencies wget libffi libffi-dev ca-certificates python3-dev postgresql-dev build-base
RUN wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3
RUN python3 --version
RUN pip3 --version
RUN pip3 install psycopg2
RUN pip3 install --upgrade pip
RUN pip3 install gunicorn
RUN pip3 install python-memcached
RUN pip3 install cryptography
RUN ls -la && ls -la / && mount
RUN git clone http://github.com/openspending/os-conductor.git app
RUN cd app && pip install -r requirements.txt
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV OS_CONDUCTOR_CACHE=cache:11211
ENV OS_API=os-api:8000
ENV OS_CONDUCTOR=os-conductor:8000

ADD startup.sh /startup.sh
ADD secrets /secrets

EXPOSE 8000

CMD echo working from $WORKDIR && cd $WORKDIR && echo OS-CONDUCTOR DB: $OS_CONDUCTOR_ENGINE && chmod +x /startup.sh && sync && /startup.sh
