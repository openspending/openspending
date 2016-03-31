#!/bin/bash
docker-compose -f build.yml kill
docker-compose -f build.yml up -d
docker-compose -f build.yml logs
./sync-shared-folders.sh
