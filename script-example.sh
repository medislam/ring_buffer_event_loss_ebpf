#!/bin/bash


fout="result/dd_file"


mkdir result

for (( i = 0; i < 1; i++ )); do


	sudo sync; echo 3 > /proc/sys/vm/drop_caches

	echo "running bcc"
	sudo python3 example-ring-buffer-lost-event.py -t dd > result/dd_trace &

	sleep 3
	echo "running dd with 10 process ..." 

	for (( j = 0; j < 10; j++ )); do
		dd if=/dev/urandom of=$fout$j bs=4k count=100000 conv=fdatasync oflag=direct 2> result/dd-result$i &
	done

	sleep 3

	PID=`pidof dd`
	while s=`ps -p $PID`; do
	    sleep 1
	done
	echo "dd is finished ..." 

	sudo kill $(pidof python3) 2> /dev/null
	echo "bcc is stopped ..." 
	
	sudo cp /sys/kernel/tracing/trace_pipe result/trace_pipe	

done 