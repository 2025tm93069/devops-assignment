FROM nginxinc/nginx-unprivileged:stable-alpine

COPY default.conf /etc/nginx/conf.d/default.conf
COPY upstreams/blue.conf /etc/nginx/upstreams/active.conf

USER 101:101
