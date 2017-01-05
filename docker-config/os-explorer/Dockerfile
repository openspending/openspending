FROM node:7-alpine

RUN apk add --update git
RUN update-ca-certificates
RUN git clone http://github.com/openspending/os-explorer.git app
RUN cd app && npm install && npm run build
#RUN cd app && (find . -type f | grep -v /public/ | grep -v index.html | grep -v config.json | grep -v favicon.ico | tee | xargs rm) | true

RUN rm -rf /var/cache/apk/*

COPY startup.sh /startup.sh

EXPOSE 8000

CMD /startup.sh
