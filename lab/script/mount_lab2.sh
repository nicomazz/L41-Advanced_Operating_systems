#!/bin/bash
echo "Mounting lab2"

sudo sshfs -o allow_other,IdentityFile=/home/nicomazz/.ssh/2018-2019-l41-insecure-private-key.txt root@192.168.141.100:/data/lab2 /mnt/beagle


