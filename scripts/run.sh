#!/bin/bash

set -e

. scripts/prepare.sh

debug=

if [[ $1x == __debugx ]]; then
    shift
    host=$1
    shift
    export pydev_host=${host}
    debug=true
fi

export PG_HOST=pg
export REDIS_HOST=redis

echo "ENVIRONMENT:"
env

command=$1
shift
args=$@

echo ""
echo "COMMAND: ${command} ${args}"

if [[ -n ${debug} ]];  then
    host=$(ip route get 1 | awk '{print $NF;exit}')
    echo "Debugger will try to connect to: ${pydev_host}"
fi

python ${command} ${args}
