import json
from collections import defaultdict

import pygraphviz as pgv
from IPython.display import Image
from dtrace import *

from test import setup_kernel, save_output, convert_in_bandwith, plot_graph, read_json_file

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
        printf("{\\"timestamp\\": %u, \\"local_port\\": %u, \\"foreign_port\\": %u, \\"previous_tcp_state\\": \\"%s\\", \\"tcp_state\\": \\"%s\\"}", 
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
                label = "server" if value["local_port"] == TARGET_PORT else "client"

                # print "State transition {} -> {}".format(
                #    value['previous_tcp_state'], value['tcp_state'])
            else:
                print "String malformatted missing previous_tcp_state of tcp_state fields"
        except ValueError as e:  # stack trace
            prec_f = "\n".join([i.replace('`', '+').split("+")[1] for i in raw_value.split('\n')[1:2]][::-1])
            tcp_state_machine.add_edge(from_state, to_state,
                                       label=label + "\n({})".format(prec_f), color='green')

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


def benchmark_tcp_bandwith(latencies=[], flags="", dtrace_script=speed_benchmark, output_name="", quiet=False,
                           trials=10):
    values = []

    def simple_out(value):
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
    cmd("sleep 2")
    program_outputs = []

    # Display header to indicate that the benchmarking has started
    for latency in latencies:
        set_latency(latency)
        if not quiet: print("Latency: {}".format(latency))
        for i in range(trials):
            cmd("sysctl net.inet.tcp.hostcache.purgenow=1")

            ipc_cmd = "ipc/ipc-static -i tcp -B -b 1048576 -q {} 2thread".format(flags)
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
        "latencies": latencies,
        "output": values,
        "program_outputs": program_outputs
    }

    if len(output_name) > 0:
        save_output(result, output_name)

    return result

def plot_tcp_bandwidth(input_data_file,
                       title=None,
                       label=None,
                       trials=10,
                       save_name=None,
                       axis=None,
                       y_label=None,
                       x_label=None
                       ):
    # Plot the read performance (IO bandwidth against buffer size with error bars)
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    xvs = data['latencies']
    total_size = 16 * 1024 * 1024
    read_performance_values = [int(i) for i in data['output']]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = convert_in_bandwith(read_performance_values, total_size)

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
    "snd_cwnd": "args[3]->snd_cwnd",
    "snd_wnd": "args[3]->snd_wnd",
    "th_seq": "(unsigned int)args[1]->th_seq",
    "th_dport": "htons(args[1]->th_dport)",
    "timestamp": "vtimestamp",
    "th_sport": "htons(args[1]->th_sport)",
    "th_ack": "(unsigned int)args[1]->th_ack",
    "snd_ssthresh": "args[3]->snd_ssthresh"
}

print_all_variables_d_script = """
#pragma D option bufsize=3M
#pragma D option bufresize=manual

fbt::tcp_do_segment:entry
/args[1]->th_sport == htons(10141) || args[1]->th_dport == htons(10141)/
{ 
""" + "\n".join(
    ["printf(\"{}:%d\",{});".format(key, value) for key, value in tcp_variables.items()]) + """
}
"""


def benchmark_variables(latency=10, flags="", output_name=""):
    return benchmark_tcp_bandwith(
        latencies=[latency],
        dtrace_script=print_all_variables_d_script,
        trials=1,
        flags=flags,
        output_name=output_name)


def extract_tcp_variables(input_name):
    data = read_json_file(input_name)
    output = data["output"]
    res = defaultdict(list)
    for s in output:
        ss = s.split(":")
        res[ss[0]].append(int(ss[1]))
    return res


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


def smooth_avg(xvs,yvs, factor = 20, times = 10):
    for _ in range(times):
        yvs = [avg(yvs[i:i+factor]) for i in range(len(yvs)-factor)]
        yvs += [yvs[-1]] * factor
    return xvs,yvs

def copied_bandwidth(times, seq, time_diffs=0.0001):

    final_len = 0
    TIME_SPLIT = 150
    cur_time = times[0]  # float(ENTRIES[0]["Time"])
    cur_seq = seq[0]  # float(ENTRIES[0]["Seq"])
    bws = []
    unit_ctr = 0
    for e in zip(times, seq):
        diff = ((float(e[0]) - cur_time) / 1000000000)
        if diff > time_diffs:
            bws.append(e)
            cur_time = float(e[0])

    bws = zip(bws[::2], bws[1::2])

    tps = []
    for e in bws:
        tp = (float(e[1][1]) - float(e[0][1])) / (float(e[1][0]) - float(e[0][0]))
        tps.append(max(tp, 0))

    times = [list(b)[1][0] for b in bws]
    times = [(float(t) - float(times[0])) / 1000000000 for t in times]
    return smooth_avg(times, tps)


## resolution in milliseconds
def plot_tcp_bandwidth_across_time(input_name, title=None, resolution=100, sender_side=True):
    tmp = extract_tcp_variables(input_name)
    initial_size = len(tmp["timestamp"])
    if sender_side:
        tmp = filter_input(tmp, "th_dport", TARGET_PORT)
    else:
        tmp = filter_input(tmp, "th_sport", TARGET_PORT)
    assert len(tmp["timestamp"]) < initial_size
    variables = tmp

    time = variables["timestamp"]
    maxt = time[-1]
    time = [t-maxt for t in time]

    seq = variables["th_seq"]
    xvs, yvs = copied_bandwidth(time,seq) #easy_bandwidth(time, seq)  # compute_bandwidth(time, seq)
    max_time = xvs[-1] / 1e9
    x_ticks = [0.1 * i for i in range(int(max_time / 0.1))]

    print("Data prepared. Now plotting..")
    return plot_graph(
        xvs=[t / 1e9 for t in xvs],
        yvs=yvs,
        trials=1,
        title=title,
        x_ticks=x_ticks
    )


def plot_variable(input_name, var, title=None, ax=None, sender_side=True, filter_maximum = False):
    tmp = extract_tcp_variables(input_name)
    if sender_side:
        tmp = filter_input(tmp, "th_dport", TARGET_PORT)
    else:
        tmp = filter_input(tmp, "th_sport", TARGET_PORT)
    variables = tmp  # filter_resolution(tmp)

    time = variables["timestamp"]
    yvs = variables[var]
    if filter_maximum:
        yvs = [i if i < 1e6 else 0 for i in yvs]
    offset = time[0]
    time = [i - offset for i in time]
    max_time = time[-1] / 1e9
    x_ticks = [0.1 * i for i in range(int(max_time / 0.1))]

    print("Data prepared. Now plotting {}..".format(var))

    return plot_graph(
        label=var,
        xvs=[t/1e9 for t in time],
        yvs=yvs,
        trials=1,
        title=title,
        axis=ax,
        x_ticks=x_ticks
    )


def plot_all_variables(input_name):
    ax = None
    for var, _ in tcp_variables.items():
        ax = plot_variable(input_name, var, ax=ax)
    return ax
