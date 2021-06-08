#!/usr/bin/python3

import sys
import time

from bcc import BPF
import ctypes as ct

import argparse
import sys 
from subprocess import check_output 


# arguments
examples ="""
	./bcc_iotracer.py -t task_name 
	# trace task (specified by its name)
"""


parser = argparse.ArgumentParser(
    description="Trace vfs_write",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)

parser.add_argument("-t", "--task",
                    help="trace this task only")


args = parser.parse_args()
name = args.task


# Define eBPF program
program=("""
	#include <linux/fs.h>
	#include <linux/aio.h>
	#include <linux/uio.h>


	struct event{
    	u64 	timestamp;
	};

	BPF_RINGBUF_OUTPUT(buffer, 4);

	ssize_t VFS_write(struct pt_regs *ctx,struct file * file, const char __user * buf, size_t count, loff_t * pos){
		
		if(FILTER_CMD){
	    	char 	comm2[16];
			char comm1[16] = "REPLACE_CMD";
			bpf_get_current_comm(&comm2, sizeof(comm2));
			for (int i = 0; i < sizeof(comm1); ++i)
	    		if (comm1[i] != comm2[i])
	    			return 0;
    	}

		struct event event = {};

		event.timestamp = bpf_ktime_get_ns();

		if(buffer.ringbuf_output(&event, sizeof(event), 0) == -EAGAIN){
			bpf_trace_printk("EAGAIN");
		}
		
		return 0;
	}

""")


# code replacements

if args.task:
    program = program.replace('FILTER_CMD', '1')
    program = program.replace('REPLACE_CMD', '%s' % name)
    #print("REPLACE_CMD")

else:
    print("you must specify the traced cmd")
    sys.exit()



b = BPF(text = program)

# Attach kprobes to the functions
b.attach_kprobe(event="vfs_write", fn_name="VFS_write")



# ------------------ Report traces to user -----------------------
# -------------------------------------------------------------------------
#print("Pour stopper eBPF ..... Ctrl+C")

# callback parses messages received from perf_buffer_poll
def callback(ctx, data, size):
    evenement = b["buffer"].event(data)	
    event = (evenement.timestamp)
    format_ = ("%.0f")
    print(format_ % event)


b["buffer"].open_ring_buffer(callback)


try:
    while 1:
        # b.ring_buffer_poll()
        b.ring_buffer_consume()
        # time.sleep(1)
except KeyboardInterrupt:
    sys.exit()