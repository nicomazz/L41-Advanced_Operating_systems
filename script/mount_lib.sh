!#/bin/bash
echo "Mounting lib in lab2"

sudo sshfs -o allow_other,IdentityFile=/home/nicomazz/.ssh/2018-2019-l41-insecure-private-key.txt root@192.168.141.100:/data/lab2/lib ~/MEGAsync/uni1920/OS/lab/lib 

