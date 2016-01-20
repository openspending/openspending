#!/bin/bash
docker-compose --x-networking -f dev.yml up
./sync-shared-folders.sh
