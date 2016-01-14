#!/bin/bash
ssh s145 -fN -L4444:$OS_DB_HOST:5432
