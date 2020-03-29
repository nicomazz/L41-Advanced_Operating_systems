/*records thigs received/sent from/to server*/
fbt::tcp_do_segment:entry
/args[1]->th_sport == htons(10141) || args[1]->th_dport == htons(10141)/
{
	printf("source:%d ", htons(args[1]->th_sport));
	printf("dest:%d ", htons(args[1]->th_dport));
	printf("Seq:%d ", (unsigned int)args[1]->th_seq);
	printf("Ack:%d ", (unsigned int)args[1]->th_ack);
	printf("Time:%d ", walltimestamp);
	printf("wnd:%d ", args[3]->snd_wnd);
	printf("cwnd:%d ", args[3]->snd_cwnd);
	printf("ssthresh:%d ", args[3]->snd_ssthresh);
	/*trace(tcp_state_string[args[3]->t_state]);*/
}