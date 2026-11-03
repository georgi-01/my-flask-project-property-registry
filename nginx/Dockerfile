FROM nginx:1.30-alpine
RUN apk add --no-cache openssl \
 && mkdir -p /etc/nginx/certs \
 && openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost" \
      -keyout /etc/nginx/certs/localhost.key -out /etc/nginx/certs/localhost.crt
COPY default.conf /etc/nginx/conf.d/default.conf
