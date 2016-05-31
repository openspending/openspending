#!/bin/bash
echo 'now uploading:'
#docker save `docker images --format "{{.ID}}" openspending/redash:latest` | sudo docker-squash -t openspending/redash -verbose | docker load
for x in `docker images --format "{{.Repository}}" | grep openspending/` ; do
    echo $x;
    docker push $x ;
done
