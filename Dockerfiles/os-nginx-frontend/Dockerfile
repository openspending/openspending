FROM sickp/alpine-nginx


WORKDIR /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY server-rules.conf /etc/nginx/server-rules.conf
COPY startup.sh /startup.sh

COPY 500.html /usr/share/nginx/errors/500.html

EXPOSE 80

CMD ["/startup.sh"]
