import json

import pygraphviz as pgv
from IPython.display import Image
from dtrace import *


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
            #print(value)
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
