#!/bin/bash

while ! nc -z pg 5432; do echo "waiting for postgres " && sleep 3; done
while ! nc -z redis 6379; do echo "waiting for redis" && sleep 3; done

exec $@
