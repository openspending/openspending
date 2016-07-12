FROM gliderlabs/alpine:3.4


RUN apk add --update python git nodejs
RUN apk add --update --virtual=build-dependencies ca-certificates build-base
RUN update-ca-certificates
RUN cd $(npm root -g)/npm \
 && npm install fs-extra \
 && sed -i -e s/graceful-fs/fs-extra/ -e s/fs\.rename/fs.move/ ./lib/utils/rename.js
RUN npm install npm@latest -g
RUN npm --version
RUN git clone http://github.com/openspending/os-packager.git app
RUN cd app && npm install
RUN cd app && npm install
RUN cd app && node node_modules/gulp/bin/gulp.js
RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ENV OS_PACKAGER_BASE_PATH=packager

ADD settings.json /app/settings.json
ADD startup.sh /startup.sh

EXPOSE 8000

CMD OS_CONDUCTOR="http://${OS_EXTERNAL_ADDRESS}" /startup.sh
