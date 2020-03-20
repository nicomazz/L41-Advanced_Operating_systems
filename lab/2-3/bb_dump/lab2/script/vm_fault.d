
BEGIN {
    in_benchmark = 0;
    cstart = 0;
}

syscall::clock_gettime:return
/execname == "ipc-static" && in_benchmark <= 0/
{
    in_benchmark++;
    cstart = in_benchmark == 1 ? timestamp : cstart;
}
syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;
}
fbt::vm_fault:entry
/execname == "ipc-static" && in_benchmark/
{
   self->ts = vtimestamp;
}

fbt::vm_fault:return
/execname == "ipc-static"
        && self->ts
        && in_benchmark/
{
/*      @faults = quantize(vtimestamp - self->ts); */
        @times["times"] = sum(vtimestamp - self->ts);
        @counts["counts"] = count();
}
