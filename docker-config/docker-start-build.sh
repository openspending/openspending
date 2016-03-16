#!/bin/bash
docker-compose -f build.yml kill
docker-compose -f build.yml up
./sync-shared-folders.sh
