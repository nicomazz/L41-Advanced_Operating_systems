# Lab 1

## Introduction

It is superscalar, so there might be interesting behavious

In this lab only syscall provider

The aggregation will reduce the probe effect

How to reduce the probe effect: remove output?

2 configurations: benchmark configuration without instrumentation, and with
dtrace. But when using dtrace the performance will be different. So that we have
to describe the probe effect. But we don't have to minimize it

Why ipc buffer size affects the system call overhead?

## to make it work trough ssh:
```
ifconfig # to find the correct interface
sudo ifconfig enp0s21f0u1i2 192.168.141.102 # to give me an ip addr
ssh root@192.168.141.100
```

Library used:
`https://github.com/tmetsch/python-dtrace`
