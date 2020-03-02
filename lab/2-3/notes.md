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
- [x] it may be sensible to inspect quantize() results for both the execution time distributions of the system calls, and the amount of data returned by each
- [x] investigate scheduling events using the sched provider ( on-cpu and off-cpu events)
- [x] instrument sleep and wakeup
- [x] take care about pid and tid
- [ ] probe effect: one simple way to approach the problem is to analyse the results of performance benchmarking with and without DTrace scripts running, and compare the ascii output of the script
- [ ] read the FreeBSD Benchmarking Advice wiki 
- [ ] plot intervals for on-cpu and off-cpu events
   - [ ] correctly label the graph

### questions to answer
- How does increasing IPC buffer size uniformly change performance across IPC models – and why?
- Explore the impact of the probe effect on your causal investigation; how has DTrace changed the behavior of the benchmark?

## Practical things to do
- [ ] measure page fault with vminfo. try to run this: `dtrace -P vminfo'/execname == "soffice.bin"/{@[probename] = count()}'`
- [ ] number of syscalls and traps for each case (line graph)
   - [ ] number of read syscall and write syscalls for each buffer size (line graph)
   - [ ] instrument traps with fbt::abort_handler:entry
- [x] Graph with the off-cpu time for each buffer size (line graph)
- [x] Partial read writes:
   - [x] show only an example of the aggregation: in a bar graph, the number of each write call and the 
         number of read for a specific example
   - [x] on a graph, number of reads and number of writes for each buffer size (bar)
- [x] Understand how to measure the dtrace probe effect
   running the benchmark with and without dtrace
### PMC
- [x] Graph l1d_refill for each size
- [x] graph l2_hit for each size
- [x] graph cycles per instr
- [x] graph axi_read and write
- [x] graph mem_write_per_cycle and read
- [ ] show how the dtrace instrumentation changes the ratio cycle/instructions (In the same graph, put with dtrace instumentation with a dotted line)
- [ ] find a reason for each inflection point


## Additional things, if there is time
- [ ] time spent in vm_fault/pmap fault (check script) for each buffer size (line graph)
- [ ] lock contention ( see scripts)

# Lab 3 - Performance monitoring counters



## Further things to do for the report

### kernel things
- [x] comment the small errors
- [x] comment that I remove the first result, even if it is not true
- [x] traps count graph in the document
- [x] write that pipes don't have to handle reordering or things like that, but sockets do
- [x] Plot the performance without dtrace running in the same graph as the one with dtrace running, but dotted
- [x] !!! ATTENTION: by mistake, my vm_fault graph  is the same as the trap one. it is to do again
- [ ] Make the vm faults count and traps count graphs like squares, so they fit better.
- [ ] Put the cpu tracing of reads and writes at the right of the page
- [ ] put the graph "bandwith_during_scheduling_recording.png", showing the dtrace effect while tracing schduling events. Also "bandwith_during_trap_recording.png"
- [ ] put a line in the first overall graph on each interesting point (l1 cache, l2 cache, tlb)
- [ ] update off_cpu_times in the report with "off_cpu_time_all.png"
- [ ] off-time cpu: update graph in the report, and comment the point at 8K
- [ ] update vm_fault.png with the new corrected one, and do the trials 10 times!
- [ ] graph for time in vm_fault
- [ ] measure time spent in vm faults

### pmc things
- [x] write what pmc are in methodology
- [ ] Discuss horizontal instruction count and flex point at 8KB for local (pmc_instr.png)
- [ ] Discuss memory writes and read per instruction
- [ ] discuss L1 cache refills (pmc_l1_refill.png)
- [ ] !! discuss AXI-bus read/write transaction vs buffer size
- [ ] memory reads are in cache lines, so 32bytes at time, take this into account
- [ ] discuss "pmc_execution_overhead.png"

