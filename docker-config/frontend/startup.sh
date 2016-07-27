#!/bin/sh
set -e

echo "HELLO WORLD!"

while ! ping -c1 os-api &>/dev/null; do :; done && echo "OS-API is UP"
while ! ping -c1 os-conductor &>/dev/null; do :; done && echo "OS-CONDUCTOR is UP"
while ! ping -c1 os-packager &>/dev/null; do :; done && echo "OS-PACKAGER is UP"
while ! ping -c1 os-viewer &>/dev/null; do :; done && echo "OS-VIEWER is UP"
while ! ping -c1 os-admin &>/dev/null; do :; done && echo "OS-ADMIN is UP"
while ! ping -c1 os-fdp-adapters &>/dev/null; do :; done && echo "OS-FDP-ADAPTERS is UP"
while ! ping -c1 landing &>/dev/null; do :; done && echo "LANDING is UP"
while ! ping -c1 redash &>/dev/null; do :; done && echo "REDASH is UP"
while ! ping -c1 celery-flower &>/dev/null; do :; done && echo "FLOWER is UP"

echo "NGINX STARTING"
nginx -g "daemon off;"
