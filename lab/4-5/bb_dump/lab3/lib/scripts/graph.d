fbt::syncache_add:entry,
fbt::syncache_expand:entry
/ 1 == 0/
{
    print(*args[2]);
}

fbt::tcp_do_segment:entry
{
     printf("%X",args[1]->th_flags);
     trace((unsigned int)args[1]->th_seq);
     trace((unsigned int)args[1]->th_ack);
     trace(tcp_state_string[args[3]->t_state]);
 }
fbt::tcp_state_change:entry
{
    printf("newstate: %s",tcp_state_string[args[1]]);
}

fbt::tcp_state_change:entry
/0 == 1/
{
     printf("{\"timestamp\": %u, \"local_port\": %u, \"foreign_port\": %u, \"previous_tcp_state\": \"%s\", \"tcp_state\": \"%s\"}",
     walltimestamp,
     ntohs(args[0]->t_inpcb->inp_inc.inc_ie.ie_lport),
     ntohs(args[0]->t_inpcb->inp_inc.inc_ie.ie_fport),
     tcp_state_string[args[0]->t_state],
     tcp_state_string[args[1]]);
     stack();
 }
