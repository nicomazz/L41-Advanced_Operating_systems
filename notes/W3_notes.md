# The process model
Robert Watson

## The process model

The multics process model is taken as reference.

posix_spawn now replaces fork, from mac os 10

`procstat -v PID`
C: copy on write: by default it is not copyied, but only when written it is.
df: default pager
ld-elf.so.1 is the runtime linker

`objdump -p binary`
to inspect the ELF binary

## virtual memory

The infinite amount of virtual memory can be splitted into kernel and user at a
specific point.
The kernel has always the same address space

## Run-time linker

- static linking is basically never used anymore. A lot of good reasons to not
  do that, such as patching of vulns
- dynamic linking is slighly slower, but reduces code duplication
  Three activityies:
   - Load ELF segments
   - relocation
   - Resolve symbols (PLT program linkage table)

`ldd bin` tells which are the dependencies of the program
`procstat -x PID`

## Traps and syscall

- Trap: transitioning from a ring to another
- syscall: a trap that make userspace seem to call a function in the kernel, and
  the kernel to receive a function call

vdso?

From the syscall.master a lot of other things are generated (such as dtrace
tracepoints

profile-997 because 997 is a prime number and doesn't interfere with the dimer

The amount of time went zeroing the new page
