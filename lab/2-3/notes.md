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
- [ ] Graph with the off-cpu time for each buffer size (line graph)
- [ ] number of syscalls and traps for each case (line graph)
   - [ ] number of read syscall and write syscalls for each buffer size (line graph)
- [ ] same graph with sleep and wakeup"
- [ ] Partial read writes:
   - [ ] show only an example of the aggregation: in a bar graph, the number of each write call and the 
         number of read for a specific example
   - [ ] on a graph, number of reads and number of writes for each buffer size (bar)
- [ ] Understand how to measure the dtrace probe effect
### PMC
- [x] Graph l1d_refill for each size
- [ ] graph l2_hit for each size
- [ ] graph l2_hit_per_cycle for each size
- [ ] graph dtlb_refill for each size
- [ ] graph cycles per instr
- [ ] graph axi_read and write
- [ ] graph mem_write_per_cycle and read



## Additional things, if there is time
- [ ] time spent in vm_fault/pmap fault (check script) for each buffer size (line graph)
- [ ] lock contention ( see scripts)
- [ ] page faults

# Lab 3 - Performance monitoring counters



## Further things to do for the report

- [ ] comment the small errors
- [ ] Discuss horizontal instruction count and flex point at 8KB for local (pmc_instr.png)
- [ ] discuss L1 cache refills (pmc_l1_refill.png)
- [ ] !! discuss AXI-bus read/write transaction vs buffer size

-
