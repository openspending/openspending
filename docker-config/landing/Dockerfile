FROM nginx:alpine

RUN rm /etc/nginx/nginx.conf /etc/nginx/mime.types

RUN apk add --update git
RUN update-ca-certificates
RUN git clone http://github.com/openspending/landing.git app

COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types
COPY default /etc/nginx/sites-enabled/default

EXPOSE 8000

CMD 'nginx'
