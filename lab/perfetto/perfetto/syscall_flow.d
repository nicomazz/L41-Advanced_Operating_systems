/*#pragma D option flowindent*/

BEGIN {
    cstart = 0;
}


syscall:::
/execname == "ipc-static" && self->i++ < 1000/
{
   self->time = timestamp;
   printf("%s %s ts: %d tid: %d pid: %d depth: %d\n", probefunc, probename, timestamp,tid,pid,stackdepth);
}

