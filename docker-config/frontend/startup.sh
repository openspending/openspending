#!/bin/bash
set -e

while ! ping -c1 os-api &>/dev/null; do :; done && echo "OS-API is UP"
while ! ping -c1 os-conductor &>/dev/null; do :; done && echo "OS-CONDUCTOR is UP"
while ! ping -c1 os-packager &>/dev/null; do :; done && echo "OS-PACKAGER is UP"
while ! ping -c1 os-viewer &>/dev/null; do :; done && echo "OS-VIEWER is UP"

echo "NGINX STARTING"
nginx -g "daemon off;"
