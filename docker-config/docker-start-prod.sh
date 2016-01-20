#!/bin/bash
#TODO make sure that OS_API_ENGINE is defined
docker-compose --x-networking -f production.yml up -d
