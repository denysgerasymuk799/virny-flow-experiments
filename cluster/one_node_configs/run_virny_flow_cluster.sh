#!/bin/bash

NUM_WORKERS=$1
SESSION=$2
EMAIL=$3

# Start the task manager
echo -e 'Starting TaskManager...'
python ../scripts/run_task_manager.py --exp_config_yaml_path /home/$EMAIL/projects/virny-flow-experiments/logs/$SESSION/exp_config.yaml > ./$SESSION/task_manager.log 2>&1 &

# Start worker processes
echo -e 'Starting Workers...'
for i in $(seq 1 $NUM_WORKERS); do
    (
      python ../scripts/run_worker.py --exp_config_yaml_path /home/$EMAIL/projects/virny-flow-experiments/logs/$SESSION/exp_config.yaml
    ) > ./$SESSION/worker_$i.log 2>&1 &
done

# Wait for all background processes to finish
wait
