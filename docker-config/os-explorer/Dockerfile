FROM nginx:alpine

RUN rm /etc/nginx/nginx.conf /etc/nginx/mime.types

RUN apk add --update git nodejs
RUN update-ca-certificates
RUN git clone http://github.com/openspending/os-explorer.git app
RUN npm install npm -g
RUN npm --version
RUN cd app && npm install
RUN cd app && node node_modules/.bin/gulp
RUN cd app && (find . -type f | grep -v /public/ | grep -v index.html | grep -v config.json | grep -v favicon.ico | tee | xargs rm)

RUN rm -rf /var/cache/apk/*

COPY startup.sh /startup.sh
COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types
COPY default /etc/nginx/sites-enabled/default

EXPOSE 8000

CMD /startup.sh
