#pragma D option flowindent

BEGIN {
    in_benchmark = 0;
    cstart = 0;
    write_finished = 0;
}


syscall::clock_gettime:return
/execname == "ipc-static" && in_benchmark <= 0/
{
    in_benchmark++;
    cstart = in_benchmark == 1 ? timestamp : cstart;
}

syscall::write:entry
/execname == "ipc-static" && in_benchmark > 0 && write_finished == 0/
{
   write_start = timestamp;
   in_write = 1;
}
syscall::write:return
/execname == "ipc-static" && in_benchmark > 0/
{
   write_finished = 0;
   in_write = 0;
}

sched:::on-cpu
/execname == "ipc-static" && in_benchmark > 0 && in_write/
{
   self->start_on_cpu = timestamp - write_start;
   /*printf("tid %d oncpu %d", tid, timestamp - write_start);*/
}

sched:::off-cpu
/execname == "ipc-static" && in_benchmark > 0 && in_write/
{
   printf("%d %d %d", tid, self->start_on_cpu, timestamp - write_start);
}

syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;

     /*printf("LOOP ended -> tid: %d, pid: %d, total_time: %d", tid, pid, timestamp - cstart);
     trace(timestamp - cstart);*/
}
