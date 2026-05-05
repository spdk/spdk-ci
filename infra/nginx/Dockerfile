FROM nginx:1.29.8

# Remove sym links from nginx image
# These by default redirect to /dev/stdout and /dev/stderr
RUN rm /var/log/nginx/access.log
RUN rm /var/log/nginx/error.log

RUN apt-get update && apt-get -y install logrotate

COPY nginx-logrotate.conf /etc/logrotate.d/nginx

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD [ "/entrypoint.sh" ]
