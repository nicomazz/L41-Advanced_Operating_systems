import json
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import imp

try:
    imp.find_module('dtrace')
    from dtrace import *
except ImportError:
    print("DTrace module missing!")


def dummy_f(cmd):
    return "Don't forget to call set_exec_callback from the jupyter notebook!"


cmd = dummy_f


def set_exec_callback(c):
    global cmd
    cmd = c


def testa():
    print cmd("ls")


def buffers_up_to_16MB():
    return [1024 * 2 ** exp for exp in range(0, 15)]


def setup_kernel():
    return cmd("sysctl kern.ipc.maxsockbuf=33554432")


def save_output(result, output_name):
    with open(output_name, 'w') as f:
        f.write(json.dumps(result, indent=2))

    return result


def benchmark(flags, trials, buff_sizes, dtrace_script, output_name="",
              quiet=False):
    values = []
    aggr_dict = defaultdict(int)

    def simple_out(value):
        values.append(value)

    def walk_func(a, b, c, d):
        pass
        # aggr_dict[c[0]] += d

    # print_header(["Starting io-static performance measurement",flags])

    # Create a seperate thread to run the DTrace instrumentation
    setup_kernel()
    dtrace_thread = DTraceConsumerThread(dtrace_script,
                                         chew_func=lambda v: None,
                                         chewrec_func=lambda v: None,
                                         out_func=simple_out,
                                         walk_func=walk_func,
                                         sleep=1)

    # Start the DTrace instrumentation
    dtrace_thread.start()

    program_outputs = []

    # Display header to indicate that the benchmarking has started
    for size in buff_sizes:
        if not quiet:
            print("buffer size:", size, "collected so far: ", len(values))
        for i in range(trials):
            # !!! -B flag removed
            ipc_cmd = "ipc/ipc-static -b {} {} 2thread".format(str(size), flags)
            output = cmd(ipc_cmd)
            program_outputs.append(str("\n".join(output)))
            # if len(output) > 0 and not quiet:
            #    print( "output:",output)

    # The benchmark has completed - stop the DTrace instrumentation
    dtrace_thread.stop()
    dtrace_thread.join()
    dtrace_thread.consumer.__del__()

    if not quiet:
        print "values collected: {}".format(len(values))

    result = {
        "buffer_sizes": buff_sizes,
        "output": values,
        "aggr_dict": aggr_dict,
        "program_outputs": program_outputs
    }

    if len(output_name) > 0:
        save_output(result, output_name)

    return result


def benchmark_single_output_aggregation(flags, trials, buff_sizes,
                                        dtrace_script, output_name="",
                                        quiet=False):
    total_res = {
        "buffer_sizes": [],
        "output": [],
        "aggr_dict": [],
        "program_outputs": []
    }
    if not quiet:
        print "benchmark single output aggregation with flags: {}".format(flags)
    for sz in buff_sizes:
        if not quiet:
            print "benchmarking buffer size: {}".format(sz)

        for t in range(trials):
            while True:
                res = benchmark(
                    flags=flags,
                    trials=1,
                    buff_sizes=[sz],
                    dtrace_script=dtrace_script,
                    quiet=quiet
                )
                new_lines = res['output']
                if len(new_lines) >= 2:
                    break
                print "!!! error, new lines in benchmark are not 2"
                print "\n".join(res['output'])

            if not quiet:
                print "{} new output lines".format(len(res['output']))
            for key in total_res:
                total_res[key] += res[key]

    total_res['buffer_sizes'] = buff_sizes

    if len(output_name) > 0:
        save_output(total_res, output_name)
    return total_res


def get_default_color(label):
    if label is None: return None

    dc = [
        ("local -s", 'limegreen'),
        ("local", 'darkorange'),
        ("pipe", 'cornflowerblue'),
        ("snd_cwnd", 'limegreen'),
        ("snd_ssthresh", 'darkorange'),
        ("pipe", 'cornflowerblue'),
        ("tcp -s", 'darkorange'),
        ("tcp", 'cornflowerblue'),
        ("window", 'red')
    ]
    for (k, v) in dc:
        if k in label:
            return v
    return None


def plot_graph(xvs,  # x values
               yvs,  # y values
               title=None,
               label=None,
               trials=10,
               save_name=None,
               axis=None,
               y_label=None,
               x_label=None,
               color=None,
               linestyle=None,
               figsize=(15, 6),
               x_ticks=None,
               alpha=1.0,
               linewidth=None
               ):
    print "xvs len:", len(xvs), "yvs len:", len(yvs), "trials:", trials

    # Reshape the list into an array of size [len(BUFFER_SIZES), NUM_TRIALS]
    io_bandwidth = np.reshape(yvs, (len(xvs), trials))[:, :]

    # Convert the array of io bandwidth values into a Panda DataFrame
    # this allows ploting of the median value and computation of the
    # error bars (25 and 75 percentile values)
    # Note: The error bars should be small indicating that the experiment is tightly controlled
    df = pd.DataFrame(io_bandwidth, index=xvs)

    # Compute error bars based on the 25 and 75 quartile values
    error_bars = df.quantile([.25, .75], axis=1)
    error_bars.loc[[0.25]] = df.median(1) - error_bars.loc[[0.25]]
    error_bars.loc[[0.75]] = error_bars.loc[[0.75]] - df.median(1)
    error_bars_values = [error_bars.values]

    # Create and label the plot
    if color is None:
        color = get_default_color(label)

    if axis is None:
        fig = plt.figure(figsize=figsize)
    #     ax = df.median(1).plot(yerr=error_bars_values, title=title, label=label,
    #                            color=color, linestyle=linestyle, alpha=alpha,
    #                            linewidth=linewidth)
    # else:
    ax = df.median(1).plot(yerr=error_bars_values, title=title, ax=axis,
                           label=label, color=color, alpha=alpha,
                           linewidth=linewidth,
                           linestyle=linestyle)

    if title:
        plt.title(title)  # 'io-static {} performance'.format(label))
    if y_label:
        ax.set_ylabel(y_label)
    if x_label:
        ax.set_xlabel(x_label)

    if len(xvs) >= 2 and xvs[1] == xvs[0] ** 2:
        ax.set_xscale('log')

    if x_ticks is None:
        x_ticks = xvs
    # ax.ticklabel_format(useOffset=False)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(["{}".format(i) for i in x_ticks])

    plt.grid('on', axis='x')
    plt.grid('on', axis='y')

    plt.legend()

    if save_name:
        plt.savefig(save_name)

    return ax


def read_json_file(file_name):
    with open(file_name, 'r') as f:
        content = f.read()
        return json.loads(content)


def plot_aggregation(input_data_file,
                     title=None,
                     label=None,
                     trials=10,
                     save_name=None,
                     axis=None,
                     y_label=None,
                     x_label=None,
                     figsize=None):
    # in aggregations the output is one line yes and one no
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1]  # 16*1024*1024
    values = [int(i) for i in data['output'][::2]]

    return plot_graph(
        xvs=buffer_sizes,
        yvs=values,
        title=title,
        label=label,
        trials=trials,
        save_name=save_name,
        axis=axis,
        y_label=y_label,
        x_label=x_label,
        figsize=figsize
    )


def convert_in_bandwith(values, total_size):
    return [(total_size / 1024) / (val / 1e9) for val in values]


def plot_bandwith(input_data_file,
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
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1]  # 16*1024*1024
    read_performance_values = [int(i) for i in data['output']]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = convert_in_bandwith(read_performance_values,
                                              total_size)

    return plot_graph(
        xvs=buffer_sizes,
        yvs=io_bandwidth_values,
        title=title,
        label=label,
        trials=trials,
        save_name=save_name,
        axis=axis,
        y_label=y_label,
        x_label=x_label
    )


def extract_pmc_val(s, name):
    res = re.search(r"^\s*{}: (.*)$".format(name), s, re.M)
    if res:
        return res.group(1)
    print "Error extracting pmc value, value {} not in s".format(name)
    return 0


def plot_pmc(input_data_file,
             pmc_to_plot,
             title=None,
             label=None,
             trials=10,
             save_name=None,
             axis=None,
             y_label=None,
             x_label=None,
             figsize=None,
             linestyle='-'):
    # Plot the read performance (IO bandwidth against buffer size with error bars)
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1]  # 16*1024*1024
    program_outs = data['program_outputs']

    read_performance_values = [float(extract_pmc_val(i, pmc_to_plot)) for i in
                               program_outs]

    return plot_graph(
        xvs=buffer_sizes,
        yvs=read_performance_values,
        title=title,
        label=label,
        trials=trials,
        save_name=save_name,
        axis=axis,
        y_label=y_label,
        x_label=x_label,
        linestyle=linestyle,
        figsize=figsize
    )


def latency_name(lat):
    return "all_variables_{}.json".format(lat)


def latency_name_s(lat):
    return "all_variables_{}_s.json".format(lat)


def plot_time(input_data_file,
              title=None,
              label=None,
              trials=10,
              save_name=None,
              axis=None,
              y_label="IPC Bandwith (KB/s)",
              x_label="Buffer size (KB)",
              dotted=True
              ):
    # Plot the read performance (IO bandwidth against buffer size with error bars)
    data = read_json_file(input_data_file)

    # Buffer sizes to compute the performance with
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1]  # 16*1024*1024
    program_outs = data['program_outputs']

    read_performance_values = [float(extract_pmc_val(i, "time")) * 1e9 for i in
                               program_outs]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = convert_in_bandwith(read_performance_values,
                                              total_size)

    return plot_graph(
        xvs=buffer_sizes,
        yvs=io_bandwidth_values,
        title=title,
        label=label,
        trials=trials,
        save_name=save_name,
        axis=axis,
        y_label=y_label,
        x_label=x_label,
        linestyle="--" if dotted else "-"
    )


def plot_cnt_graph(xvs,  # x values
                   cnt1y,  # y values,
                   cnt2y,
                   title=None,
                   label=None,
                   save_name=None,
                   y_label=None,
                   x_label=None
                   ):
    plt.figure(figsize=(15, 6))
    p1 = plt.bar(xvs, cnt1y, 0.35, label="1")
    p2 = plt.bar(xvs, cnt2y, 0.35, bottom=cnt1y, label="2")

    if title:
        plt.title(title)  # 'io-static {} performance'.format(label))
    if y_label:
        plt.ylabel(y_label)
    if x_label:
        plt.xlabel(x_label)

    plt.set_xscale('log')
    plt.set_xticks(xvs)
    plt.set_xticklabels([i / 1024 for i in xvs], rotation=0)

    plt.grid('on', axis='x')
    plt.grid('on', axis='y')

    plt.legend()

    if save_name:
        plt.savefig(save_name)

    return ax


def benchmark_without_dtrace(name_prefix, script="BEGIN{}",
                             additional_flags=""):
    buffer_sizes = buffers_up_to_16MB()
    trials = 10
    modes = ["local", "local -s", "pipe"]

    for mode in modes:
        flags = "-i {} -v {}".format(mode, additional_flags)
        out_name = "{}_{}{}.json".format(name_prefix, mode, additional_flags)

        print "mode: ", mode, "flags:", flags, "out_name:", out_name

        res = benchmark(
            flags=flags,
            trials=trials,
            output_name=out_name,
            buff_sizes=buffer_sizes,
            dtrace_script=script
        )


def benchmark_probe_effect(name_prefix, script="BEGIN{}", additional_flags=""):
    buffer_sizes = buffers_up_to_16MB()
    trials = 10
    modes = ["local", "local -s", "pipe"]

    for mode in modes:
        flags = "-i {} -v {}".format(mode, additional_flags)
        out_name = "{}_{}{}.json".format(name_prefix, mode, additional_flags)

        print "mode: ", mode, "flags:", flags, "out_name:", out_name

        res = benchmark(
            flags=flags,
            trials=trials,
            output_name=out_name,
            buff_sizes=buffer_sizes,
            dtrace_script=script
        )


def tttt():
    plot_pmc(input_data_file="",
             pmc_to_plot="time",
             title="Performance measurement without DTrace running",
             label=mode,
             trials=10,
             save_name=None,
             axis=None,
             y_label="Bandwith",
             x_label="Buffer size")
