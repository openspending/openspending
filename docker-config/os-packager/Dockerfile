FROM gliderlabs/alpine:latest

RUN apk add --update python
RUN apk add git
RUN apk add nodejs
RUN git clone http://github.com/openspending/os-packager.git app
RUN cd app && npm install --only=prod
RUN cd app && npm install --only=dev
RUN cd app && node node_modules/gulp/bin/gulp.js
RUN rm -rf /var/cache/apk/*

ENV OS_PACKAGER_BASE_PATH=packager/

ADD settings.json /app/settings.json
ADD startup.sh /startup.sh

EXPOSE 8000

CMD echo working from $WORKDIR && cd $WORKDIR && OS_CONDUCTOR="http://${OS_EXTERNAL_ADDRESS}" /startup.sh
