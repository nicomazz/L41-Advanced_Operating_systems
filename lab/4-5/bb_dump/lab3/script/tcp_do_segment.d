fbt::tcp_do_segment:entry {
	trace((unsigned int)args[1]->th_seq);
	trace((unsigned int)args[1]->th_ack);
	trace(tcp_state_string[args[3]->t_state]);
}
