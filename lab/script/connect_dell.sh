#!/bin/bash

(sudo ifconfig enp0s20f0u1i2 192.168.141.102 || sudo ifconfig enp0s20f0u3i2 192.168.141.102) && echo "Ip set!"


