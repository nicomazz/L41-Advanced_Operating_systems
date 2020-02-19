
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
    /* trace(timestamp - cstart);
   printf("tid: %d, pid: %d, time: %d", tid, pid, vtimestamp - self->cstart);*/
}

syscall::read:return 
/execname == "ipc-static" && in_benchmark > 0/
{
    @read = quantize(arg0);
    @tot_r = sum(arg0);
}

syscall::write:return 
/execname == "ipc-static"  && in_benchmark > 0/
{
    @write = quantize(arg0);
    @tot_w = sum(arg0);
}

syscall::exit:entry
/execname == "ipc-static" && in_benchmark <= 0/
{
    printf("pid: %d", pid);
    printf("Read aggregation:");
    printa(@read);
    printf("write aggregation:"); 
    printa(@write);
    
    printf("total read, write:");
    printa(@tot_r); printa(@tot_w);
    
    clear(@tot_r); clear(@tot_w);
    clear(@read); clear(@write);
    printf("##################################"); 
    in_benchmark = 0;

}

END
{
    printf("in the end:");
    printa(@read); printa(@write);	
    exit(0);
}
