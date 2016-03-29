#!/bin/bash
echo 'now uploading:'
for x in `docker images --format "{{.Repository}}" | grep openspending/` ; do echo $x; docker push $x ; done
