#!/bin/bash

set -e

apt-get update
apt-get install -y python-dev build-essential python-pip
pip install --upgrade pip virtualenv
apt-get install -y libxml2-dev libxslt1-dev libncurses5-dev libssl-dev libyaml-dev \
  libmysqlclient-dev libpq-dev libmongo-client-dev librabbitmq-dev\
  libevent-dev libffi-dev git

