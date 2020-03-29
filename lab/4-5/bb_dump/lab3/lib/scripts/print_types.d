fbt::tcp_do_segment:entry
/args[1]->th_sport == htons(10141) || args[1]->th_dport == htons(10141)/
{
print(*args[1]);
print(*args[3]);
	exit(0);
}

/*
struct tcphdr {
    u_short th_sport = 0x9d27
    u_short th_dport = 0x1896
    tcp_seq th_seq = 0x6e0e1290
    tcp_seq th_ack = 0xa79a5193
    unsigned char th_x2 :4 = 0
    unsigned char th_off :4 = 0xa
    u_char th_flags = 0x12
    u_short th_win = 0xffff
    u_short th_sum = 0
    u_short th_urp = 0
}

struct tcpcb {
    struct tsegqe_head t_segq = {
        struct tseg_qent *lh_first = 0
    }
    void *[2] t_pspare = [ 0, 0 ]
    int t_segqlen = 0
    int t_dupacks = 0
    struct tcp_timer *t_timers = 0xc3ce0200
    struct inpcb *t_inpcb = 0xc3cb3af8
    int t_state = 0x2
    u_int t_flags = 0x2a0
    struct vnet *t_vnet = 0
    tcp_seq snd_una = 0xa79a5192
    tcp_seq snd_max = 0xa79a5193
    tcp_seq snd_nxt = 0xa79a5193
    tcp_seq snd_up = 0xa79a5192
    tcp_seq snd_wl1 = 0
    tcp_seq snd_wl2 = 0
    tcp_seq iss = 0xa79a5192
    tcp_seq irs = 0
    tcp_seq rcv_nxt = 0
    tcp_seq rcv_adv = 0xffff
    u_long rcv_wnd = 0
    tcp_seq rcv_up = 0
    u_long snd_wnd = 0
    u_long snd_cwnd = 0x3fffc000
    u_long snd_spare1 = 0
    u_long snd_ssthresh = 0x3fffc000
    u_long snd_spare2 = 0
    tcp_seq snd_recover = 0xa79a5192
    u_int t_rcvtime = 0x80065647
    u_int t_starttime = 0
    u_int t_rtttime = 0x80065647
    tcp_seq t_rtseq = 0xa79a5192
    u_int t_bw_spare1 = 0
    tcp_seq t_bw_spare2 = 0
    int t_rxtcur = 0x12c
    u_int t_maxseg = 0x218
    u_int t_pmtud_saved_maxseg = 0
    int t_srtt = 0
    int t_rttvar = 0x4b0
    int t_rxtshift = 0
    u_int t_rttmin = 0x3
    u_int t_rttbest = 0
    u_long t_rttupdated = 0
    u_long max_sndwnd = 0
    int t_softerror = 0
    char t_oobflags = '\0'
    char t_iobc = '\0'
    u_char snd_scale = 0
    u_char rcv_scale = 0
    u_char request_r_scale = 0xa
    u_int32_t ts_recent = 0
    u_int ts_recent_age = 0
    u_int32_t ts_offset = 0
    tcp_seq last_ack_sent = 0
    u_long snd_cwnd_prev = 0
    u_long snd_ssthresh_prev = 0
    tcp_seq snd_recover_prev = 0
    int t_sndzerowin = 0
    u_int t_badrxtwin = 0
    u_char snd_limited = 0
    int snd_numholes = 0
    struct sackhole_head snd_holes = {
        struct sackhole *tqh_first = 0
        struct sackhole **tqh_last = 0xc3ce00e8
    }
    tcp_seq snd_fack = 0
    int rcv_numsacks = 0
    struct sackblk [6] sackblks = [
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        },
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        },
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        },
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        },
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        },
        struct sackblk {
            tcp_seq start = 0
            tcp_seq end = 0
        }
    ]
    tcp_seq sack_newdata = 0
    struct sackhint sackhint = {
        struct sackhole *nexthole = 0
        int sack_bytes_rexmit = 0
        tcp_seq last_sack_ack = 0
        int ispare = 0
        int sacked_bytes = 0
        uint32_t [1] _pad1 = [ 0 ]
        uint64_t [1] _pad = [ 0 ]
    }
    int t_rttlow = 0
    u_int32_t rfbuf_ts = 0x488a84
    int rfbuf_cnt = 0
    struct toedev *tod = 0
    int t_sndrexmitpack = 0
    int t_rcvoopack = 0
    void *t_toe = 0
    int t_bytes_acked = 0
    struct cc_algo *cc_algo = 0xc08f8a90
    struct cc_var *ccv = 0xc3ce02f8
    struct osd *osd = 0xc3ce0310
    u_int t_keepinit = 0
    u_int t_keepidle = 0
    u_int t_keepintvl = 0
    u_int t_keepcnt = 0
    u_int t_tsomax = 0
    u_int t_tsomaxsegcount = 0
    u_int t_tsomaxsegsize = 0
    u_int t_flags2 = 0x2
    uint32_t [8] t_ispare = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
    struct tcp_function_block *t_fb = 0xc08fc11c
    void *t_fb_ptr = 0
    void *[2] t_pspare2 = [ 0, 0 ]
    uint64_t [6] _pad = [ 0, 0, 0, 0, 0, 0 ]
}

*/