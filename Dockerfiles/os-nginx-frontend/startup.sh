#!/bin/sh
set -e

echo "CHECKING DEPENDENT SERVICES!"

while ! ping -c1 os-api &>/dev/null; do :; done && echo "OS-API is UP"
while ! ping -c1 os-conductor &>/dev/null; do :; done && echo "OS-CONDUCTOR is UP"
while ! ping -c1 os-packager &>/dev/null; do :; done && echo "OS-PACKAGER is UP"
while ! ping -c1 os-viewer &>/dev/null; do :; done && echo "OS-VIEWER is UP"
while ! ping -c1 os-explorer &>/dev/null; do :; done && echo "OS-EXPLORER is UP"
while ! ping -c1 os-admin &>/dev/null; do :; done && echo "OS-ADMIN is UP"
while ! ping -c1 os-fdp-adapters &>/dev/null; do :; done && echo "OS-FDP-ADAPTERS is UP"

echo "NGINX STARTING"
nginx -g "daemon off;"
