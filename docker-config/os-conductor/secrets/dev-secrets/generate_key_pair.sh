#!/bin/bash
openssl genrsa -out .tmpkey 2048
openssl rsa -in .tmpkey -out private.pem -outform pem
openssl rsa -in .tmpkey -out public.pem -outform pem -pubout
rm .tmpkey
