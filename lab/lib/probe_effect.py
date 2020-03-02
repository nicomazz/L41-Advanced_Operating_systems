
def benchmark_without_dtrace():
    for mode in modes:
        for pmc in pmcs:

            flags = "-i {} -P {}".format(mode,pmc)
            out_name = generate_name(mode=mode, pmc=pmc)

            print "mode: ",mode, "pmc:",pmc, "flags:", flags, "out_name:",out_name

            res = benchmark(
                flags=flags,
                trials=TRIALS,
                output_name=out_name,
                buff_sizes=BUFFER_SIZES,
                dtrace_script=dummy_dtrace_script
            )