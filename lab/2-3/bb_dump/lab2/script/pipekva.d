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

fbt::*pipe*:
/execname == "ipc-static" && self->i++ < 20/
{
   trace(arg0);
   trace(arg1);
   trace(arg2);
  /* printf("subtract_long(amount:%d,sub:%d)", arg0, arg1);
*/
}

syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;
     /*printf("LOOP ended -> tid: %d, pid: %d, total_time: %d", tid, pid, timestamp - cstart);
     trace(timestamp - cstart);*/
}
