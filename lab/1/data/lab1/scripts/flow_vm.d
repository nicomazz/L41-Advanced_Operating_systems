#pragma D option flowindent

BEGIN {
}

syscall::clock_gettime:return
/execname == "io-static" && !self->in_benchmark/
{
    self->in_benchmark = 1;
    self->cstart = vtimestamp;
}

syscall::clock_gettime:entry
/execname == "io-static" && self->in_benchmark/
{
    self->in_benchmark = 0;
    trace(vtimestamp - self->cstart);
}

syscall::execve:return
/execname == "io-static" && !self->in_benchmark/
{
    /* self->in_benchmark = 1; */
    self->star_time = vtimestamp;
}

syscall::exit:entry
/execname == "io-static" && self->in_benchmark/
{
    self->in_benchmark = 0;
    printf("tot %d",timestamp - self->star_time); 
}


fbt::vn_io_*:
/self->in_benchmark/ /* && self->i++ < 1000/ */
{
	@[probefunc] = count();
}
