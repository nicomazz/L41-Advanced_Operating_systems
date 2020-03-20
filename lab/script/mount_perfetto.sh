#!/bin/bash

echo "Mounting remote /data/perfetto in ~/Projects/perfetto/beaglebone"
sudo sshfs -o allow_other,IdentityFile=/home/carlazz/.ssh/2018-2019-l41-insecure-private-key root@192.168.141.100:/data/perfetto /home/carlazz/Projects/perfetto/beaglebone

