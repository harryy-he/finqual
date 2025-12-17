import finqual as fq
import cProfile
import pstats
from memory_profiler import memory_usage
import time

start = 2020
end = 2024
quarter = 3  # For quarterly data

# -----------------------------------------------------------------------

ticker = "NVDA"

fq_ticker = fq.Finqual(ticker)
fq_cca = fq.CCA(ticker)

# cProfiling

profiler = cProfile.Profile()
profiler.enable()

df_bs_p = fq_ticker.balance_sheet_period(start_year=start, end_year=end, quarter=False).to_pandas()
df_cc_pp = fq_cca.profitability_ratios_period(start_year=start, end_year=end).to_pandas()

profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats("cumtime").print_stats(30)


# ---

def load_financials():
    # This function will be called in a child process
    return fq_cca.profitability_ratios_period(start_year=start, end_year=end).to_pandas()


if __name__ == '__main__':

    start = time.time()
    mem_usage = memory_usage(load_financials, interval=0.1)
    end = time.time()

    peak_mem = max(mem_usage) - min(mem_usage)  # in MB
    duration = end - start  # in seconds
    mem_time_product = peak_mem * duration

    print(f"Peak memory: {peak_mem:.1f} MB")
    print(f"Duration: {duration:.2f} s")
    print(f"Memory × Time: {mem_time_product:.1f} MB·s")
