#!/bin/bash

# Rewrite default server configuration with our template
envsubst '${SH_SHARE_SERVICE_DOMAIN} ${SH_SHARE_SERVICE_SHADOW}' < "$@" > /etc/nginx/conf.d/default.conf

echo "Starting with configuration:"
find /etc/nginx -type f -name '*.conf'
echo "Starting with SSH keys:"
find /etc/nginx -type f -name '*.PEM' -o -name '*.pem' 

exec nginx -g 'daemon off;'
