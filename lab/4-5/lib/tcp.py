import imp
import json
from bisect import bisect_left
from collections import defaultdict

import pygraphviz as pgv
from IPython.display import Image

try:
    imp.find_module('dtrace')
    from dtrace import *
except ImportError:
    pass  # print("DTrace module missing!")

from test import setup_kernel, save_output, convert_in_bandwith, plot_graph, \
    read_json_file, get_default_color, extract_pmc_val

TARGET_PORT = 10141


def dummy_f(cmd):
    return "Don't forget to call set_exec_callback from the jupyter notebook!"


cmd = dummy_f


def set_tcp_exec_callback(c):
    global cmd
    cmd = c


def set_latency(latency=10):
    cmd("ipfw pipe config 1 delay {}".format(str(latency)))
    cmd("ipfw pipe config 2 delay {}".format(str(latency)))


def setup_pipes(latency=10):
    set_latency(latency)
    cmd("ifconfig lo0 mtu 1500")
    cmd("ipfw add 1 pipe 1 tcp from any 10141 to any via lo0")
    cmd("ipfw add 2 pipe 2 tcp from any to any 10141 via lo0")


"""
 fbt::tcp_do_segment:entry {
        trace((unsigned int)args[1]->th_seq);
        trace((unsigned int)args[1]->th_ack);
        trace(tcp_state_string[args[3]->t_state]);
    }
"""


def graph_tcp(latency):
    set_latency(latency)

    tcp_state_change_script = """
 /*
   fbt::tcp_do_segment:entry {
        trace((unsigned int)args[1]->th_seq);
        trace((unsigned int)args[1]->th_ack);
        trace(tcp_state_string[args[3]->t_state]);
    }
    */
    fbt::tcp_state_change:entry {
        printf("{\\"timestamp\\": %u, \\"local_port\\": %u, 
        \\"foreign_port\\": %u, \\"previous_tcp_state\\": \\"%s\\", 
        \\"tcp_state\\": \\"%s\\"}", 
        walltimestamp,
        ntohs(args[0]->t_inpcb->inp_inc.inc_ie.ie_lport),
        ntohs(args[0]->t_inpcb->inp_inc.inc_ie.ie_fport),
        tcp_state_string[args[0]->t_state],
        tcp_state_string[args[1]]);

        stack();
    }
    """

    # Callback invoked to process the aggregation
    values = []

    def simple_out(raw_value):
        values.append(raw_value)

    # Create a seperate thread to run the DTrace instrumentation
    dtrace_thread = DTraceConsumerThread(tcp_state_change_script,
                                         out_func=simple_out,
                                         chew_func=lambda v: None,
                                         chewrec_func=lambda v: None,
                                         walk_func=None,
                                         sleep=1)
    cmd("sysctl net.inet.tcp.hostcache.purgenow=1")
    # Start the DTrace instrumentation
    dtrace_thread.start()

    # Display header to indicate that the benchmarking has started
    print("Running ipc benchmark")

    # Run the ipc-static benchmark
    benchmark_output = cmd("ipc/ipc-static -v -i tcp 2thread")

    cmd("sleep 1")
    # The benchmark has completed - stop the DTrace instrumentation
    dtrace_thread.stop()
    dtrace_thread.join()
    dtrace_thread.consumer.__del__()

    label = "TCP state machine - {} ms latency".format(latency)
    output_file = "TCP_state_machine_{}_ms.png".format(latency)
    tcp_state_machine = pgv.AGraph(
            label=label, strict=False, directed=True)
    for raw_value in values:
        try:
            value = json.loads(raw_value)
            # print(value)
            # JSON formatted string
            if 'previous_tcp_state' in value and 'tcp_state' in value:
                from_state = value['previous_tcp_state'][6:]
                to_state = value['tcp_state'][6:]
                label = "server" if value[
                                        "local_port"] == TARGET_PORT else \
                    "client"

                # print "State transition {} -> {}".format(
                #    value['previous_tcp_state'], value['tcp_state'])
            else:
                print "String malformatted missing previous_tcp_state of " \
                      "tcp_state fields"
        except ValueError as e:  # stack trace
            prec_f = "\n".join([i.replace('`', '+').split("+")[1] for i in
                                raw_value.split('\n')[1:2]][::-1])
            tcp_state_machine.add_edge(from_state, to_state,
                                       label=label + "\n({})".format(prec_f),
                                       color='green')

            # Raw string - manually post-process
            # print "Preceeding stack frame {}".format(raw_value.split('\n')[1])

    print("Completed")
    tcp_state_machine.draw(path=output_file, format='png', prog='dot')
    return Image(output_file)


speed_benchmark = """
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
    trace(timestamp - cstart);
}

syscall::exit:entry
/execname == "ipc-static"/
{
}

"""


def benchmark_tcp_bandwith(latencies=[], flags="",
                           dtrace_script=speed_benchmark, output_name="",
                           quiet=False,
                           ignore_dtrace_output=False,
                           trials=10):
    values = []

    def simple_out(value):
        if ignore_dtrace_output:
            return
        values.append(value)

    # Create a seperate thread to run the DTrace instrumentation
    setup_kernel()
    dtrace_thread = DTraceConsumerThread(dtrace_script,
                                         chew_func=lambda v: None,
                                         chewrec_func=lambda v: None,
                                         out_func=simple_out,
                                         sleep=1)

    # Start the DTrace instrumentation
    dtrace_thread.start()
    cmd("sleep 1")
    program_outputs = []

    # Display header to indicate that the benchmarking has started
    for latency in latencies:
        set_latency(latency)
        if not quiet: print("Latency: {}".format(latency))
        for i in range(trials):
            cmd("sysctl net.inet.tcp.hostcache.purgenow=1")
            # q flag removed!! B flag removed!!
            ipc_cmd = "ipc/ipc-static -i tcp -b 1048576 {} " \
                      "2thread".format(
                    flags)
            output = cmd(ipc_cmd)
            program_outputs.append(str("\n".join(output)))

    cmd("sleep 2")
    # The benchmark has completed - stop the DTrace instrumentation
    dtrace_thread.stop()
    dtrace_thread.join()
    dtrace_thread.consumer.__del__()

    if not quiet:
        print "values collected: {}".format(len(values))

    result = {
            "latencies"      : latencies,
            "output"         : values,
            "program_outputs": program_outputs
    }

    if len(output_name) > 0:
        save_output(result, output_name)

    return result


def merge_bandwidth_files(files, output_name):
    if len(files) <= 1: return

    res = defaultdict(list)
    batches = []
    for file in files:
        data = read_json_file(file)
        xvs = data['latencies']
        total_size = 16 * 1024 * 1024
        read_performance_values = [int(i) for i in data['output']]
        res['latencies'] += xvs
        res['output'] += data['output']

    if len(output_name) > 0:
        save_output(res, output_name)


def plot_tcp_bandwidth(input_data_file,
                       title=None,
                       label=None,
                       trials=10,
                       save_name=None,
                       axis=None,
                       y_label=None,
                       x_label=None
                       ):
    # Plot the read performance (IO bandwidth against buffer size with error
    # bars)
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    xvs = data['latencies']
    total_size = 16 * 1024 * 1024
    read_performance_values = [int(i) for i in data['output']]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = convert_in_bandwith(read_performance_values,
                                              float(total_size))

    return plot_graph(
            xvs=xvs,
            yvs=io_bandwidth_values,
            title=title,
            label=label,
            trials=trials,
            save_name=save_name,
            axis=axis,
            y_label=y_label,
            x_label=x_label
    )


tcp_variables = {
        "snd_cwnd"    : "args[3]->snd_cwnd",
        "snd_wnd"     : "args[3]->snd_wnd",
        "th_seq"      : "(unsigned int)args[1]->th_seq",
        "th_dport"    : "htons(args[1]->th_dport)",
        "timestamp"   : "walltimestamp",
        "th_sport"    : "htons(args[1]->th_sport)",
        "th_ack"      : "(unsigned int)args[1]->th_ack",
        "snd_ssthresh": "args[3]->snd_ssthresh"
}

print_all_variables_d_script = """
#pragma D option bufsize=3M
#pragma D option bufresize=manual

fbt::tcp_do_segment:entry
/args[1]->th_sport == htons(10141) || args[1]->th_dport == htons(10141)/
{ 
""" + "\n".join(
        ["printf(\"{}:%d\",{});".format(key, value) for key, value in
         tcp_variables.items()]) + """
}
"""

def print_all_variables_script():
    print(print_all_variables_d_script)

def benchmark_variables(latency=10, flags="", output_name="", trials=1):
    return benchmark_tcp_bandwith(
            latencies=[latency],
            dtrace_script=print_all_variables_d_script,
            trials=trials,
            flags=flags,
            output_name=output_name)


def benchmark_tcp_without_dtrace(script=print_all_variables_d_script,
                                 name_prefix="", trials=5, modes=["", "-s"]):
    for mode in modes:
        flags = "{} -v".format(mode)
        out_name = "tcp_{}_{}_wno_dtrace.json".format(name_prefix, mode)

        print "mode: ", mode, "flags:", flags, "out_name:", out_name

        benchmark_tcp_bandwith(latencies=range(0, 41, 5), flags=flags,
                               trials=trials,
                               dtrace_script=script,
                               ignore_dtrace_output=True,
                               output_name=out_name)
        print("{} generated".format(out_name))


def plot_tcp_time_from_output(input_data_file,
                              title=None,
                              label=None,
                              trials=5,
                              save_name=None,
                              ax=None,
                              y_label="Bandwidth (KB/s)",
                              x_label="Latency(ms)",
                              dotted=True,
                              color=None
                              ):
    # Plot the read performance (IO bandwidth against buffer size with error
    # bars)
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    latencies = data['latencies']
    total_size = float(16 * 1024 * 1024)
    program_outs = data['program_outputs']

    read_performance_values = [
            float(extract_pmc_val(i, "time")) * 1e9 for i in program_outs]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = convert_in_bandwith(read_performance_values,
                                              total_size)

    return plot_graph(
            xvs=latencies,
            yvs=io_bandwidth_values,
            title=title,
            label=label,
            trials=trials,
            color=color,
            save_name=save_name,
            axis=ax,
            y_label=y_label,
            x_label=x_label,
            linestyle="--" if dotted else "-"
    )


def filter_time(variables, min, max):
    res = defaultdict(list)
    time = variables["timestamp"]

    min_inx = bisect_left(time, min + time[0])
    max_inx = bisect_left(time, max + time[0])
    for key in variables:
        res[key] = variables[key][min_inx:max_inx]
    return res


def ns(ms=None):
    if ms is not None:
        return ms * 1e6


def extract_tcp_variables(input_name):
    data = read_json_file(input_name)
    output = data["output"]
    res = defaultdict(list)
    for s in output:
        ss = s.split(":")
        res[ss[0]].append(int(ss[1]))
    # res = filter_time(res, ns(ms=100), ns(ms=500))
    return res


def filter_variables(tmp, sender_side):
    return filter_input(tmp, "th_dport", TARGET_PORT) if sender_side \
        else filter_input(tmp, "th_sport", TARGET_PORT)


# d is a dictionary of arrays
def filter_input(d, attr, src):
    source = d[attr]
    for key in d:
        d[key] = [d[key][i] for i in range(len(d[key])) if source[i] == src]
    return d


MINIMUM_RESOLUTION = 1e4


def filter_resolution(d, min_dt=MINIMUM_RESOLUTION):
    times = d["timestamp"]
    prev_t = times[0]
    res = defaultdict(list)
    for i in range(len(times)):
        t = times[i]
        if t - prev_t >= min_dt:
            for key in d:
                res[key].append(d[key][i])
            prev_t = t
    return res


ONE_MS = 1000000


def ms(n): return n * ONE_MS


def avg(l):
    return sum(l) / len(l)


def compute_bandwidth(times, seq, mean_duration=ms(25)):
    assert len(times) == len(seq) and len(times) > 1
    offset = times[0]
    times = [i - offset for i in times]

    tmp_times = []
    tmp_bw = []
    for i in range(len(times) - 1):
        dq = float(seq[i + 1] - seq[i])
        if dq < 0:
            continue
        dt = float(times[i + 1] - times[i])
        tmp_times.append(times[i] + dt / 2)
        tmp_bw.append(dq * 1e6 / dt)

    max_time = times[-1]
    inx = 0
    max_val = 0
    final_times = []
    final_bw = []
    ntimes = len(tmp_times)
    for i in range(max_time / mean_duration - ms(500) / mean_duration):
        max_val += mean_duration
        att_bwd = []
        while inx < ntimes and tmp_times[inx] < max_val:
            att_bwd.append(tmp_bw[inx])
            inx += 1
        if len(att_bwd) > 0:
            final_times.append(max_val)
            final_bw.append(avg(att_bwd))
    print("bandwidth calculated")
    return final_times, final_bw


def easy_bandwidth(times, seq, gamma=0.05):
    offset = times[0]
    times = [i - offset for i in times]

    time_seq = zip(times, seq)
    dt_time = 1e4
    prec = time_seq[0]
    prec_bw = 1
    rt, rb = [], []
    for t, s in time_seq[1:]:
        dt = float(t - prec[0])

        if dt < dt_time:
            continue
        dq = float(s - prec[1])
        if dq < 0:
            continue

        prec = (t, s)

        bw = dq * 1e6 / dt
        prec_bw = (prec_bw * (1.0 - gamma)) + bw * gamma

        rt.append(t)
        rb.append(prec_bw)
        print(prec_bw)

    # prec = (prec * (1.0 - gamma)) + bw * gamma

    return rt[1::2], rb[1::2]


def smooth_avg(xvs, yvs, factor=20, times=1):
    for _ in range(times):
        yvs = [avg(yvs[i:i + factor]) for i in range(len(yvs) - factor)]
        yvs += [yvs[-1]] * factor
    return xvs, yvs


def calc_bandwidth(times, seq):
    cur_time = times[0]
    bws = []

    for (t, s) in zip(times, seq):
        dt = t - cur_time
        if dt > 0:
            bws.append((t, s))
            cur_time = t

    res_bw = []
    res_t = []
    for ((t0, s0), (t1, s1)) in zip(bws[::2], bws[1::2]):
        dt = t1 - t0
        ds = s1 - s0
        bw = ds * 1e6 / dt
        res_t.append(t0)
        res_bw.append(max(bw, 0))

    return smooth_avg(res_t, res_bw, factor=2, times=2)


#  return res_t, res_bw  # smooth_avg(times, tps)


## resolution in milliseconds
def plot_tcp_bandwidth_across_time(input_name, axis=None, label=None,
                                   title=None,
                                   sender_side=True, save_name=None, xlim=None):
    tmp = extract_tcp_variables(input_name)
    initial_size = len(tmp["timestamp"])
    tmp = filter_variables(tmp, sender_side)
    assert len(tmp["timestamp"]) < initial_size
    variables = tmp

    time = variables["timestamp"]
    seq = variables["th_seq"]

    xvs, yvs = calc_bandwidth(time, seq)  # easy_bandwidth(time, seq)  #
    # compute_bandwidth(time, seq)
    offset = xvs[0]
    xvs = [t - offset for t in xvs]
    max_time = xvs[-1] / 1e9
    x_ticks = [0.1 * i for i in range(int(max_time * 2 / 0.1))]

    # print("Data prepared. Now plotting...")
    return plot_graph(
            xvs=[t / 1e9 for t in xvs],
            yvs=yvs,
            label=label,
            trials=1,
            title=title,
            axis=axis,
            x_ticks=x_ticks,
            xlim=xlim,
            save_name=save_name
    )


def plot_variable(input_name, var, title=None, ax=None, sender_side=True,
                  filter_maximum=False, min_window=False, xlim=None,
                  alpha=1.0, label=None, save_name=None, grid=True):
    tmp = extract_tcp_variables(input_name)
    tmp = filter_variables(tmp, sender_side)
    variables = tmp  # filter_resolution(tmp)

    time = variables["timestamp"]

    # keeps a value only if it is the minimub between cwnd and wnd
    if var == "Minimum window":
        print(
                "lengths: ", len(variables["snd_cwnd"]),
                len(variables["snd_wnd"]))
        yvs = [min(i, j) for (i, j) in
               zip(variables["snd_cwnd"], variables["snd_wnd"])]
    else:
        yvs = variables[var]
    assert (len(yvs) == len(time))

    offset = time[0]
    time = [i - offset for i in time]
    # print("t0:", time[0], "t-1:", time[-1], "diff:", time[-1] - time[0])
    max_time = float(time[-1]) / 1e9
    # print("max time: {}".format(max_time))
    x_ticks = [0.1 * i for i in range(int((max_time + 0.1) / 0.1))]
    if filter_maximum:
        inx_ok = [i for i in range(len(yvs)) if yvs[i] < 1e8]
        yvs = [yvs[i] for i in inx_ok]
        time = [time[i] for i in inx_ok]
        if len(yvs) == 0:
            return None
    # print("Data prepared. Now plotting {}..".format(var))
    if label is None:
        label = var
    return plot_graph(
            label=label,
            xvs=[t / 1e9 for t in time],
            yvs=yvs,
            trials=1,
            title=title,
            xlim=xlim,
            x_label="Time (s)",
            y_label="Bytes",
            axis=ax,
            x_ticks=x_ticks,
            alpha=alpha,
            grid=grid,
            save_name=save_name
    )


def latency_name(lat):
    return "all_variables_{}.json".format(lat)


def latency_name_s(lat):
    return "all_variables_{}_s.json".format(lat)


AUTO_BUFFER = "Auto buffer"
FIXED_BUFF = "Fixed size buffer"
BUFF_LABELS = [AUTO_BUFFER, FIXED_BUFF]  # "", "-s"

LIMITS = {
        0 : (0, 2),
        5 : (0, 1.8),
        10: (0, 2.7),
        20: (0, 4),
        40: (0, 4)
}


def limit_ax(ax, lat):
    ax.set_xlim(LIMITS[lat])


def get_packet_loss_points(file, min_cnt=3):
    tmp = extract_tcp_variables(file)
    vars = filter_variables(tmp, sender_side=True)
    past_ack = {}
    ack_putted = {""}
    result = []
    time_offset = vars["timestamp"][0]
    for (time, ack) in zip(vars["timestamp"], vars["th_ack"]):
        if ack not in past_ack:
            past_ack[ack] = []
        past_ack[ack].append(time - time_offset)

    for (ack, times) in past_ack.items():
        if len(times) >= min_cnt:
            result.append((times[0], 10))
    return result


def plot_packet_loss(file, ax, min_loss_cnt = 3,label="Packet loss"):
    packet_loss = get_packet_loss_points(file,min_cnt=min_loss_cnt)
    time = [float(i[0]) / 1e9 for i in packet_loss]
    yvs = [i[1] for i in packet_loss]
    ax2 = ax  # .twinx()
    color = get_default_color(label)
    if color is None: color = "red"
    if len(yvs) is 0:
        return ax2
    ax2.plot(time, yvs, 'ro', label=label, color=color)
    ax2.legend()
    return ax2


def plot_tcp_cwnd(latency):
    for (file, label) in zip([latency_name(latency), latency_name_s(latency)],
                             BUFF_LABELS):
        title = "Congestion window for {}ms latency ({})".format(latency, label)
        save_name = "{}_cwnd.png"
        ax = plot_variable(file, "snd_cwnd", sender_side=True,
                           filter_maximum=True)
        # plot_variable(file, "snd_ssthresh", sender_side=True,
        #               filter_maximum=True,
        #               ax=ax)
        # plot_variable(file, "snd_wnd", save_name=save_name,
        #               alpha=0.7, sender_side=True,
        #               title=title, ax=ax)
        # y_color =get_default_color("snd_ssthresh")
        # ax2.set_ylabel("ssthresh (Bytes)",color=y_color)
        # ax2.tick_params(axis='y', labelcolor=y_color)
        # ax.set_yscale("log")

        limit_ax(ax, latency)
        # limit_ax(ax2, latency)
        plot_packet_loss(file, ax, min_loss_cnt=1)
        ax.figure.savefig(save_name)

    return ax


def plot_tcp_seq(latency):
    for (file, label) in zip([latency_name(latency), latency_name_s(latency)], BUFF_LABELS)[:1]:
        ax = plot_variable(file,
                      "th_seq",
                      sender_side=False)
        #ax.set_ylim((4.12 * 1e9, 4.13 * 1e9))

def plot_tcp_ack(latency):
    axes = []

    for (file, label) in zip([latency_name(latency), latency_name_s(latency)], BUFF_LABELS):
        ax = plot_variable(file,
                      "th_ack",
                      sender_side=True)
        axes.append(ax)
    return axes
        #ax.set_ylim((4.12 * 1e9, 4.13 * 1e9))


def plot_tcp_cwnd_wnd_ssthresh(latency):
    axes = []
    for (file, label) in zip([latency_name(latency), latency_name_s(latency)],
                             BUFF_LABELS):
        title = "Congestion window, adv window and slow start " \
                "threshold " \
                "for {}ms latency ({})".format(latency, label)
        save_name = "{}_cwnd_wnd_comparison.png".format(latency)
        ax = plot_variable(file, "snd_cwnd", sender_side=True,
                           filter_maximum=True
                           )
        plot_variable(file, "snd_ssthresh", sender_side=True,
                      filter_maximum=True,
                      ax=ax)
        plot_variable(file, "snd_wnd",
                      alpha=0.5, sender_side=True,
                      title=title, ax=ax)
        # y_color =get_default_color("snd_ssthresh")
        # ax2.set_ylabel("ssthresh (Bytes)",color=y_color)
        # ax2.tick_params(axis='y', labelcolor=y_color)
        # ax.set_yscale("log")

        limit_ax(ax, latency)
        # limit_ax(ax2, latency)
        plot_packet_loss(file, ax, min_loss_cnt=3)
        ax.figure.savefig(save_name)
        axes.append(ax)

    return axes


def compare_bandwidth(latency):
    title = "TCP bandwith across time with {}ms latency".format(latency)
    save_name = "{}_bandwidth.png".format(latency)
    ax = plot_tcp_bandwidth_across_time(latency_name(latency),
                                        label=AUTO_BUFFER,
                                        sender_side=False)
    # plot_packet_loss(latency_name(latency), ax, "Packet loss (Auto)")

    plot_tcp_bandwidth_across_time(latency_name_s(latency),
                                   title=title,
                                   axis=ax,
                                   label=FIXED_BUFF,
                                   sender_side=False)
    # plot_packet_loss(latency_name_s(latency), ax, "Packet loss (Fixed)")

    limit_ax(ax, latency)
    ax.set_yscale('log')
    ax.figure.savefig(save_name)


def compare_wnd(latency):
    ax = None
    title = "Advertised window from the receiver with {}ms latency".format(
            latency)
    save_name = "{}_wnd_comparison.png".format(latency)

    ax = plot_variable(latency_name_s(latency), "snd_wnd", sender_side=True,
                       ax=ax, label=FIXED_BUFF, title=title)
    plot_packet_loss(latency_name(latency), ax, "Packet loss (Auto)")

    ax = plot_variable(latency_name(latency), "snd_wnd", sender_side=True,
                       xlim=LIMITS[latency],
                       ax=ax, label=AUTO_BUFFER)
    plot_packet_loss(latency_name_s(latency), ax, "Packet loss (Fixed)")
    limit_ax(ax, latency)
    ax.figure.savefig(save_name)

    return ax


def compare_cwnd(latency):
    ax = None
    title = "Sender congestion window with {}.ms latency".format(latency)
    save_name = "{}_cwnd_comparison.png".format(latency)
    ax = plot_variable(latency_name(latency), "snd_cwnd", title=title,
                       sender_side=True, filter_maximum=True,
                       ax=ax, label=AUTO_BUFFER)
    plot_packet_loss(latency_name(latency), ax, "Packet loss (Auto)")

    ax = plot_variable(latency_name_s(latency), "snd_cwnd", title=title,
                       sender_side=True, filter_maximum=True,
                       xlim=LIMITS[latency],
                       ax=ax, label=FIXED_BUFF)
    plot_packet_loss(latency_name_s(latency), ax, "Packet loss (Fixed)")
    limit_ax(ax, latency)
    ax.figure.savefig(save_name)

    return ax


def compare_ssthreash(latency):
    ax = None
    title = "snd_ssthresh comparison with {}.ms latency".format(latency)
    save_name = "{}_snd_ssthresh_comparison.png".format(latency)
    ax = plot_variable(latency_name(latency), "snd_ssthresh", title=title,
                       sender_side=True, filter_maximum=False,
                       ax=ax, label=AUTO_BUFFER)
    plot_packet_loss(latency_name(latency), ax, "Packet loss (Auto)")

    ax = plot_variable(latency_name_s(latency), "snd_ssthresh", title=title,
                       sender_side=True, filter_maximum=False,
                       xlim=LIMITS[latency],
                       ax=ax, label=FIXED_BUFF)
    plot_packet_loss(latency_name_s(latency), ax, "Packet loss (Fixed)")
    ax.figure.savefig(save_name)

    return ax


def compare_all(latency):
    compare_bandwidth(latency)
    compare_cwnd(latency)
    compare_wnd(latency)
    compare_ssthreash(latency)
    plot_tcp_cwnd_wnd_ssthresh(latency)
