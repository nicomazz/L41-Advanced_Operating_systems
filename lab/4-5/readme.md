# TCP lab

- `tcpcb`: tcp control block. defined here:
   <https://sourcegraph.com/github.com/freebsd/freebsd@df2262014eee4a534988dbeae57cdc02e014020c/-/blob/sys/netinet/tcp_var.h#L94>
- states definitions: https://sourcegraph.com/github.com/freebsd/freebsd@67441e15d85bfacb98815d0b7e575afed0bbba1c/-/blob/sys/netinet/tcp_fsm.h#L47:1
- MSL: Maximum segment lifetime


```c
#define	TCP_NSTATES	11

#define	TCPS_CLOSED		0	/* closed */
#define	TCPS_LISTEN		1	/* listening for connection */
#define	TCPS_SYN_SENT		2	/* active, have sent syn */
#define	TCPS_SYN_RECEIVED	3	/* have sent and received syn */
/* states < TCPS_ESTABLISHED are those where connections not established */
#define	TCPS_ESTABLISHED	4	/* established */
#define	TCPS_CLOSE_WAIT		5	/* rcvd fin, waiting for close */
/* states > TCPS_CLOSE_WAIT are those where user has closed */
#define	TCPS_FIN_WAIT_1		6	/* have closed, sent fin */
#define	TCPS_CLOSING		7	/* closed xchd FIN; await FIN ACK */
#define	TCPS_LAST_ACK		8	/* had fin and close; await FIN ACK */
/* states > TCPS_CLOSE_WAIT && < TCPS_FIN_WAIT_2 await ACK of FIN */
#define	TCPS_FIN_WAIT_2		9	/* have closed, fin is acked */
#define	TCPS_TIME_WAIT		10	/* in 2*msl quiet wait after close */
```

## TCP header
```c
/*
 * TCP header.
 * Per RFC 793, September, 1981.
 */
struct tcphdr {
	u_short	th_sport;		/* source port */
	u_short	th_dport;		/* destination port */
	tcp_seq	th_seq;			/* sequence number */
	tcp_seq	th_ack;			/* acknowledgement number */
#if BYTE_ORDER == LITTLE_ENDIAN
	u_char	th_x2:4,		/* (unused) */
		th_off:4;		/* data offset */
#endif
#if BYTE_ORDER == BIG_ENDIAN
	u_char	th_off:4,		/* data offset */
		th_x2:4;		/* (unused) */
#endif
	u_char	th_flags;
#define	TH_FIN	0x01
#define	TH_SYN	0x02
#define	TH_RST	0x04
#define	TH_PUSH	0x08
#define	TH_ACK	0x10
#define	TH_URG	0x20
#define	TH_ECE	0x40
#define	TH_CWR	0x80
#define	TH_AE	0x100			/* maps into th_x2 */
#define	TH_FLAGS	(TH_FIN|TH_SYN|TH_RST|TH_PUSH|TH_ACK|TH_URG|TH_ECE|TH_CWR)
#define	PRINT_TH_FLAGS	"\20\1FIN\2SYN\3RST\4PUSH\5ACK\6URG\7ECE\10CWR\11AE"

	u_short	th_win;			/* window */
	u_short	th_sum;			/* checksum */
	u_short	th_urp;			/* urgent pointer */
};
```

### struct tcbcb

IT is pretty long: <https://sourcegraph.com/github.com/freebsd/freebsd@7f6b5f56c043835267db0f98eb2ec083c5a0bbee/-/blob/sys/netinet/tcp_var.h#L94:1>


```
dtrace -n 'fbt::tcp_do_segment:entry {trace((unsigned int)args[1]->th_seq);trace((unsigned int)args[1]->th_ack);trace(tcp_state_string[args[3]->t_state]);}'

```

### Notes

- the tcp RFC came out in 1981, then the paper congestion avoidance and control in 1988. This was interesting
- 