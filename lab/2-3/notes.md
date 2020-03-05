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
- [x] probe effect: one simple way to approach the problem is to analyse the results of performance benchmarking with and without DTrace scripts running, and compare the ascii output of the script
- [x] read the FreeBSD Benchmarking Advice wiki 
- [ ] use perfetto to visualize the function calls

### questions to answer
- How does increasing IPC buffer size uniformly change performance across IPC models – and why?
- Explore the impact of the probe effect on your causal investigation; how has DTrace changed the behavior of the benchmark?

## Practical things to do
- [x] measure page fault with vminfo. try to run this: `dtrace -P vminfo'/execname == "soffice.bin"/{@[probename] = count()}'`
- [x] number of syscalls and traps for each case (line graph)
   - [x] number of read syscall and write syscalls for each buffer size (line graph)
   - [x] instrument traps with fbt::abort_handler:entry
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
- [x] time spent in vm_fault/pmap fault (check script) for each buffer size (line graph)
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
- [x] put the graph "bandwith_during_scheduling_recording.png", showing the dtrace effect while tracing schduling events. Also "bandwith_during_trap_recording.png"
- [x] put a line in the first overall graph on each interesting point (l1 cache, l2 cache, tlb)
- [x] graph for time in vm_fault
- [x] measure time spent in vm faults
- [x] check if there is difference between the data gathered by dtrace and the one form the benchmark output
- [x] time spend in vm faults
- [x] IPC_comparison_with_and_wno_dtrace.png in the probe effect
- [x] update overall graph
- [x] write that the time spent in vm faults grows exponentially
- [x] update overall image with vertical bars
- [x] verify when to use vtimestamp and when to use the normal one 
- [x] think if to put the overall graph with the vertical lines
- [x] line on the size of caches
- [x] vertical lines on microarchitecture things
- [x] write about perfetto int he appendix
- [ ] understand superpages and how they work, to write something more on the VM faults and traps section
- [ ] vm an important component but not huge (1s at 16MB)
- [ ] percentage of vm_fault on total execution
- [ ] connection between pcm misses and the number of memory accesses
- [ ] explain what happens at 8k for sockets, and the plane up until 32KB.
- [ ] see the tlb graph
- [ ] use the profile provider to understand where most of the time is spent
- [ ] iteration and median vs averange
- [ ] larger figures
- [ ] annotate inflection points
- [ ] structure the report based on the key behaviours
- [ ] in the initial part the time spent in syscalls is amortized
- [ ] graph with the amount of time vm_fault, and other relevant functions, for each buffer size (
   - [ ] time in uipc_send and uipc_rcvd

### pmc things
- [x] write what pmc are in methodologys
- [ ] update graphs with squared ones
- [ ] Discuss horizontal instruction count and flex point at 8KB for local (pmc_instr.png)
- [ ] Discuss memory writes and read per instruction
- [ ] discuss L1 cache refills (pmc_l1_refill.png)
- [ ] !! discuss AXI-bus read/write transaction vs buffer size
- [ ] memory reads are in cache lines, so 32bytes at time, take this into account
- [ ] discuss "pmc_execution_overhead.png"
- [ ] discuss scalability of pipes and sockets

- [ ] clock_cycles/instr_executed is interesting to explain the 64K
- [ ] from the L1_DCACHE_REFILL we can se how pipes 
- [ ] ? why does the l1_dcache_access goes up when the buffer size is very high?
- [ ] reason why at 8k the two sockets diverge is that the normal one does not use the L1 cache efficiently: it only uses a quarter of it. There are more copies from the kernel buffer to the user buffer than the other with mataching buffer? A proof might be find inspecting the number of calls of the function that copies things inside the buffer
- [ ] TLB refills are more frequentwith normal socketes after 8kb?
## from the feedback of the practise one

- [x] do only assigned work
- page zeroing is a growing expense as io buffer size increases
- Include info about variance and present IQR information
- Write about the sd card and its speed limits. 
- write the conclusions in the abstract and conclusion 
- write about the number of iterations run, and used of median vs averange
- Larger figure
- annotate inflection points and microarachitecture threashold
- Structure the report based on the various points
- dtrace effect: the mean is useless


```
In 3.1: It would be useful to be more clear on why 64K was the optimal size. The first observation is that this appears to be where system-call overhead amortization is maximized, but microarchitectural limits haven’t yet been exceeded. But then the key question is: Why 64K? This amount is 2x the size of the L1 cache, and ¼ the size of the L2 cache. The answer likely lies in two areas: (1) The granularity of our buffer sizing isn’t fine-grained enough – it would be interesting to try with 96K, for example; and (2) Since this is a memcpy() benchmark, both source and destination need to fit in the L2. You do not appear to engage with the performance collapse seen with reads from /dev/zero, which was a key challenge in this lab, since flatlining when exceeding the L2 is expected – as we hit DRAM speeds – but collapsing is not.
```
