Lab 2 and 3 makes the second assignment

2 views of VM. from the program. And the microarachitecture view
instrument the vm traps
2 threads will talk with each other in various ways

pipes can't be used for network
sockets yes

fbt: tied to the implementation:
Evaluation of the socket primitives

## General Things to do
- [x] instrument clock_gettime for the IPC loop
- [ ] it may be sensible to inspect quantize() results for both the execution time distributions of the system calls, and the amount of data returned by each
- [ ] investigate scheduling events using the sched provider ( on-cpu and off-cpu events)
- [ ] instrument sleep and wakeup
- [ ] take care about pid and tid
- [ ] probe effect: one simple way to approach the problem is to analyse the results of performance benchmarking with and without DTrace scripts running
- [ ] discard the first result
- [ ] read the FreeBSD Benchmarking Advice wiki ### questions to answer
- How does increasing IPC buffer size uniformly change performance across IPC models – and why?
- Explore the impact of the probe effect on your causal investigation; how has DTrace changed the behavior of the benchmark?

## Practical things to do
- [ ] bar Graph with buffer size vs count of read and write syscalls
- [ ] comparison between the distribution of readed bytes and written bytes (bar
  graph)
