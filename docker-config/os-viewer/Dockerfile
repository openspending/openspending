FROM gliderlabs/alpine:3.3

RUN apk add --update python git nodejs
RUN apk add --update --virtual=build-dependencies ca-certificates build-base
RUN git clone http://github.com/openspending/os-viewer.git app
RUN npm install npm -g
RUN npm --version
RUN cd app && npm install
RUN cd app && node node_modules/gulp/bin/gulp.js
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV OS_VIEWER_BASE_PATH=viewer/

ADD settings.json /app/settings.json
ADD startup.sh /startup.sh

EXPOSE 8000

CMD echo working from $WORKDIR && cd $WORKDIR && chmod +x /startup.sh && sync && API_URL="${OS_EXTERNAL_ADDRESS}" /startup.sh
