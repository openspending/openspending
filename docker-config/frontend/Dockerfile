FROM nginx

ADD nginx.conf /etc/nginx/nginx.conf
ADD server-rules.conf /etc/nginx/server-rules.conf
ADD startup.sh /startup.sh

EXPOSE 80
EXPOSE 8080

# We need to wait for the internal dns resolving to kick in
CMD ./startup.sh
