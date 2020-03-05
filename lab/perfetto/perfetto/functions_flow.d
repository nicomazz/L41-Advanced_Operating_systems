#pragma D option quiet
#pragma D option bufpolicy=fill
#pragma D option bufsize=5g
 
BEGIN {
    in_benchmark = 0;
    printf("# DTrace\n");
}

syscall::clock_gettime:return
/execname == "ipc-static" && in_benchmark <= 0/
{
    in_benchmark++;
}

syscall::clock_gettime:entry
/execname == "ipc-static" && in_benchmark > 0/
{
    in_benchmark = -1;
}

fbt:::
/in_benchmark == 10 && execname == "ipc-static" && self->i++ < 40000/
{
    printf("%s %s ts: %d tid: %d pid: %d\n", probefunc, probename, timestamp,tid,pid);
}


syscall:::
/in_benchmark > 0 && execname == "ipc-static" && self->j++ < 40000/
{
  printf("%s %s ts: %d tid: %d pid: %d j:%d\n", probefunc, probename, timestamp,tid*2,pid,self->j);
}
