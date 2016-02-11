FROM gliderlabs/alpine:latest

RUN apk add --update python
RUN apk add git
RUN apk add nodejs
RUN git clone http://github.com/openspending/os-viewer.git app
RUN cd app && npm install 
RUN cd app && node node_modules/gulp/bin/gulp.js
RUN rm -rf /var/cache/apk/*

ADD settings.json /app/settings.json
ADD startup.sh /startup.sh

EXPOSE 8000

CMD echo working from $WORKDIR && cd $WORKDIR && OS_API="http://${OS_EXTERNAL_ADDRESS}" /startup.sh
