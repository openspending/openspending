#!/bin/bash
docker-compose -f dev.yml kill
docker-compose -f dev.yml up
./sync-shared-folders.sh
