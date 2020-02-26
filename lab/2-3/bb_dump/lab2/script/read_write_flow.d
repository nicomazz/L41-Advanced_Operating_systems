#pragma D option flowindent

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

syscall::write:enter
/execname == "ipc-static" && in_benchmark > 0/
{
   in_write = 1;
}
syscall::write:return
/execname == "ipc-static" && in_benchmark > 0/
{
   in_write = 0;
}

syscall::read:,
syscall::write:
/execname == "ipc-static" && in_benchmark > 0/
{
	printf("tid: %d",tid);
}

sched:::sleep
/execname == "ipc-static" && in_benchmark > 0/
{
   sleep_t = timestamp;
   printf("tid: %d goes to sleep", tid);
 /*  stack();*/
}

sched:::wakeup
/execname == "ipc-static" && in_benchmark/
{
	printf("tid: %d wakes up after %d", tid, (timestamp-sleep_t));
}

syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;
     /*printf("LOOP ended -> tid: %d, pid: %d, total_time: %d", tid, pid, timestamp - cstart);
     trace(timestamp - cstart);*/
}
