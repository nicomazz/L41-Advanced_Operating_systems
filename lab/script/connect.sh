#!/bin/bash

(sudo ifconfig enp0s21f0u1i2 192.168.141.102 || sudo ifconfig enp0s21f0u2i2 192.168.141.102) && echo "Ip set!"


