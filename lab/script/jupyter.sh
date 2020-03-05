#!/bin/bash

ssh root@192.168.141.100 -i ~/.ssh/2018-2019-l41-insecure-private-key -t "cd /data && jupyter notebook"
