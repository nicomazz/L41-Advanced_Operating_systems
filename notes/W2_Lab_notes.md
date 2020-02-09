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


## aggregator walk

Based on node-libdtrace:

### `consumer.aggwalk(function func (varid, key, value) {})`

Snapshot and iterate over all aggregation data accumulated since the
last call to `consumer.aggwalk()` (or the call to `consumer.go()` if
`consumer.aggwalk()` has not been called).  For each aggregate record,
`func` will be called and passed three arguments:

* `varid` is the identifier of the aggregation variable.  These IDs are
  assigned in program order, starting with 1.

* `key` is an array of keys that, taken with the variable identifier,
  uniquely specifies the aggregation record.

* `value` is the value of the aggregation record, the meaning of which
  depends on the aggregating action:

  * For `count()`, `sum()`, `max()` and `min()`, the value is the
    integer value of the aggregation action

  * For `avg()`, the value is the numeric value of the aggregating action

  * For `quantize()` and `lquantize()`, the value is an array of 2-tuples
    denoting ranges and value:  each element consists of a two element array
    denoting the range (minimum followed by maximum, inclusive) and the
    value for that range.  

Upon return from `consumer.aggwalk()`, the aggregation data for the specified
variable and key(s) is removed.

Note that the rate of `consumer.aggwalk()` actually consumes the aggregation
buffer is clamed by the `aggrate` option; if `consumer.aggwalk()` is called
more frequently than the specified rate, `consumer.aggwalk()` will not
induce any additional data processing.

`consumer.aggwalk()` does not iterate over aggregation data in any guaranteed
order, and may interleave aggregation variables and/or keys.

