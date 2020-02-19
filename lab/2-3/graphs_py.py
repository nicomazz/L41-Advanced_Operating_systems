%matplotlib inline

from collections import defaultdict
import json
import re


def setup_kernel():
    !sysctl kern.ipc.maxsockbuf=33554432
# Callback invoked to print the trace record
# (that is, printf("%u", vtimestamp - self->start))

def benchmark(flags, trials, buff_sizes, dtrace_script,output_name="", quiet=False):
    values = []
    aggr_dict = defaultdict(int)

    def simple_out(value):
        values.append(value)
    
    def walk_func(a, b, c, d):
        pass
        #aggr_dict[c[0]] += d
    
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
        !sleep 1 

        if not quiet:
            print("buffer size:", size, "collected so far: ",len(values))
        for i in range(trials):
            output = !ipc/ipc-static -B -b {str(size)} {flags} 2thread
            program_outputs.append(str("\n".join(output)))
            if len(output) > 0 and not quiet:
                print( "output:",output)
            
    # The benchmark has completed - stop the DTrace instrumentation
    dtrace_thread.stop()
    dtrace_thread.join()
    dtrace_thread.consumer.__del__()

    if not quiet:
        print("values collected:", len(values))
    
    result = {
        "buffer_sizes": buff_sizes,
        "output": values,
        "aggr_dict" : aggr_dict,
        "program_outputs": program_outputs
    }

    if len(output_name) > 0:
        #with open("lab2_{}_1202.data".format(output_name), 'w') as f:
        with open(output_name, 'w') as f:
            f.write(json.dumps(result, indent=2))
                
    return result

def plot_graph(xvs, # x values
               yvs, # y values
               title = None, 
               label = None, 
               trials = 10,
               save_name = None, 
               axis = None,
               y_label = None,
               x_label = None
              ):
   
    # Reshape the list into an array of size [len(BUFFER_SIZES), NUM_TRIALS]
    io_bandwidth = np.reshape(yvs, (len(xvs), trials))[:,:]

    # Convert the array of io bandwidth values into a Panda DataFrame
    # this allows ploting of the median value and computation of the 
    # error bars (25 and 75 percentile values)
    # Note: The error bars should be small indicating that the experiment is tightly controlled
    df = pd.DataFrame(yvs, index=xvs)
   

    # Compute error bars based on the 25 and 75 quartile values
    error_bars = df.quantile([.25, .75], axis=1)
    error_bars.loc[[0.25]] = df.median(1) - error_bars.loc[[0.25]]
    error_bars.loc[[0.75]] = error_bars.loc[[0.75]] - df.median(1)
    error_bars_values = [error_bars.values]

    # Create and label the plot

    if axis is None:
        fig = plt.figure(figsize=(15,6))
        ax = df.median(1).plot(yerr=error_bars_values, title=title, label = label)
    else:
        ax = df.median(1).plot(yerr=error_bars_values, title=title, ax=axis, label = label)
    
    if title:
        plt.title(title)#'io-static {} performance'.format(label))
    if y_label:
        ax.set_ylabel(y_label)
    if x_label:
        ax.set_xlabel(x_label)
        
    ax.set_xscale('log')
    ax.set_xticks(buffer_sizes)
    ax.set_xticklabels([i/1024 for i in buffer_sizes], rotation=0)
    
    plt.grid('on', axis='x' )
    plt.grid('on', axis='y' )

    plt.legend()
   

    if save_name:
        plt.savefig(save_name)
        
    return ax

def plot_bandwith(input_data_file, 
               title = None, 
               label = None, 
               trials = 10,
               save_name = None, 
               axis = None,
               y_label = None,
               x_label = None
              ):
    # Plot the read performance (IO bandwidth against buffer size with error bars)
    with open(input_data_file, 'r') as f:
        content = f.read()
        data = json.loads(content)

    # Buffer sizes to compute the performance with
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1] #16*1024*1024
    read_performance_values = [int(i) for i in data['output']]

    # Compute the IO bandwidth in KiBytes/sec
    io_bandwidth_values = [(total_size/1024)/(val/1e9) for val in read_performance_values]
    io_bandwidth_avg = [sum(io_bandwidth_values[i*trials:(i+1)*trials])/trials for i in range(len(buffer_sizes))]

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
               title = None, 
               label = None, 
               trials = 10,
               save_name = None, 
               axis = None,
               y_label = None,
               x_label = None):
    # Plot the read performance (IO bandwidth against buffer size with error bars)
    with open(input_data_file, 'r') as f:
        content = f.read()
        data = json.loads(content)

    # Buffer sizes to compute the performance with
    buffer_sizes = data['buffer_sizes']
    total_size = buffer_sizes[-1] #16*1024*1024
    program_outs = data['program_outputs']
    
    read_performance_values = [int(extract_pmc_val(i,pmc_to_plot)) for i in program_outs]

    return plot_graph(
       xvs=buffer_sizes,
       yvs=read_performance_values,
       title=title,
       label=label,
       trials=trials,
       save_name=save_name,
       axis=axis,
       y_label=y_label,
       x_label=x_label
    )
    