#!/bin/bash
docker-machine ssh default 'sudo /bin/sh -c "echo 3 > /proc/sys/vm/drop_caches && echo OK"'
