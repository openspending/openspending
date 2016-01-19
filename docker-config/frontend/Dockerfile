FROM nginx

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# We need to wait for the internal dns resolving to kick in
CMD sleep 20 && echo "NGINX STARTING" && nginx -g "daemon off;"
