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



syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;
     /*printf("LOOP ended -> tid: %d, pid: %d, total_time: %d", tid, pid, timestamp - cstart);
     trace(timestamp - cstart);*/
}

fbt::*pipe*:,
fbt::*uiomove*:,
fbt::wakeup:,
fbt::*lock*:
/execname == "ipc-static" && in_benchmark && self->i++ < 1000/ 
{
	@[probefunc] = count(); 
}

