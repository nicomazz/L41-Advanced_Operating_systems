# L41: Advanced operating systems

Robert N. M. Watson

something that allows a machine to provide services
rules and constraints on what is possible to do (enforcing

- Microkernel?
- Boxplots
- Superscalar

# Lecture 2: tracing

Facility: a service
Dynamic implementation: We don't know at compile time what we want to implement
Production system: it has to work also outside debug systems
- unified and safe: even if you try do do bad things, you can't
- Zero *Probe effect*
- dozen of providers

- dtmalloc is an abstraction: if using only fbt then we must take care about the
  names of functions

when asking to caracterize the probe effect: the effect the script had on system performance
`netinet` for the tcp stack
