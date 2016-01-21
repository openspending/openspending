FROM nginx

ADD nginx.conf /etc/nginx/nginx.conf
ADD startup.sh /startup.sh

EXPOSE 80

# We need to wait for the internal dns resolving to kick in
CMD ./startup.sh
