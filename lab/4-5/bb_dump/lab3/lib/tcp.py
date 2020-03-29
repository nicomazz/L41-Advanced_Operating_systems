import json
from collections import defaultdict

import pygraphviz as pgv
from IPython.display import Image
from dtrace import *

from test import setup_kernel, save_output, convert_in_bandwith, plot_graph, read_json_file


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
   fbt::syncache_add:entry {
   }
   fbt::syncache_expand:entry{
   }
   
   fbt::tcp_do_segment:entry {
        trace((unsigned int)args[1]->th_seq);
        trace((unsigned int)args[1]->th_ack);
        trace(tcp_state_string[args[3]->t_state]);
    }
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

    # Start the DTrace instrumentation
    dtrace_thread.start()

    # Display header to indicate that the benchmarking has started
    print("Running ipc benchmark")

    # Run the ipc-static benchmark
    benchmark_output = cmd("ipc/ipc-static -v -i tcp 2thread")

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
            if value['previous_tcp_state'] is not None and value['tcp_state'] is not None:
                from_state = value['previous_tcp_state'][6:]
                to_state = value['tcp_state'][6:]
                label = "server" if value["local_port"] == 10141 else "client"

                # print "State transition {} -> {}".format(
                #    value['previous_tcp_state'], value['tcp_state'])
            else:
                print "String malformatted missing previous_tcp_state of tcp_state fields"
        except ValueError as e:  # stack trace
            prec_f = "\n".join([i.replace('`', '+').split("+")[1] for i in raw_value.split('\n')[1:]][::-1])
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

    program_outputs = []

    # Display header to indicate that the benchmarking has started
    for latency in latencies:
        set_latency(latency)
        if not quiet: print("Latency: {}".format(latency))

        for i in range(trials):
            # !!! -B flag removed
            ipc_cmd = "ipc/ipc-static -i tcp -B -q {} 2thread".format(flags)
            output = cmd(ipc_cmd)
            program_outputs.append(str("\n".join(output)))

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


wnd_cwnd_sshth = """
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
}
"""


def benchmark_variables(latency=0, flags="", output_name=""):
    return benchmark_tcp_bandwith(
        latencies=[latency],
        dtrace_script=wnd_cwnd_sshth,
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


def compute_bandwidth(times, seq):
    assert len(times) == len(seq) and len(times) > 1
    bandwiths = []
    for i in range(len(times) - 1):
        dq = float(seq[i + 1] - seq[i])
        dt = float(times[i + 1] - times[i])
        bandwiths.append(dq * 1e6 / dt)
    bandwiths.append(bandwiths[-1])
    return bandwiths


def plot_tcp_bandwith_with_time(input_name, title=None):
    variables = extract_tcp_variables(input_name)
    time = variables["Time"][::300]
    seq = variables["Seq"][::300]
    bandwidth = compute_bandwidth(time, seq)
    offset = time[0]
    time = [i - offset for i in time]
    return plot_graph(
        xvs=time,
        yvs=bandwidth,
        trials=1,
        title=title
    )


def plot_variables(input_name, variables=["Seq", "Ack", "wnd", "Cwnd", "sshresh"]):
    variables = extract_tcp_variables(input_name)
    xvs = variables["time"]
