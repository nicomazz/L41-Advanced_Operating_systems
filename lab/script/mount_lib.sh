#!/bin/bash

echo "Mounting remote /data/lab2/lib in uni1920/OS/lab/lib"
sudo sshfs -o allow_other,IdentityFile=/home/nicomazz/.ssh/2018-2019-l41-insecure-private-key.txt root@192.168.141.100:/data/lab2/lib ~/MEGAsync/uni1920/OS/lab/lib 

