#pragma D option stackframes=100
#pragma D option bufsize=100g
#pragma D option aggsize=100g

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

profile-97
/execname =="ipc-static" && arg0 && in_benchmark > 0/
{ 
@times= count();
@[stack()] = count(); } 

syscall::exit:entry
/execname == "ipc-static"/
{
	exit(0);
}
tick-60s { exit(0);} 

