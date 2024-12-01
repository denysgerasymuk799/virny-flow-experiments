#!/bin/bash

num_workers=$1

# Start the task manager
echo -e 'Starting TaskManager...'
python ../scripts/run_task_manager.py > ./task_manager.txt 2>&1 &

# Start worker processes
echo -e 'Starting Workers...'
for i in $(seq 1 $num_workers); do
    python ../scripts/run_worker.py > ./worker_$i.txt 2>&1 &
done

# Wait for all background processes to finish
wait
