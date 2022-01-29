import os
import psutil
import time


# inner psutil function
def process_memory():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss


def bytesToMB(bytes):
    return float(round(bytes * 1e-6, 5))


# decorator function
def profile(func):
    def wrapper(*args, **kwargs):
        mem_before = process_memory()
        start = time.time()
        result = func(*args, **kwargs)
        mem_after = process_memory()
        global mem_usage
        mem_usage = bytesToMB(mem_after - mem_before)
        print("Performance stats for func_name: ", func.__name__)
        print("\tConsumed memory: free_mem_before={} mb, free_mem_after={} mb, used_mem={} mb".format(
            bytesToMB(mem_before), bytesToMB(mem_after), mem_usage))
        global total_time
        total_time = time.time() - start
        print("\tExecution time: %.7f ms" % (total_time))
        return result

    return wrapper
