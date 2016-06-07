#!/bin/bash
#TODO make sure that OS_API_ENGINE is defined
docker-compose -f production.yml stop
docker-compose -f production.yml up -d
