#!/bin/bash

num_workers=$1

# Start the task manager
python ../scripts/run_task_manager.py &

# Start worker processes
for i in {1..$num_workers}; do
    python ../scripts/run_worker.py &
done

# Wait for all background processes to finish
wait
