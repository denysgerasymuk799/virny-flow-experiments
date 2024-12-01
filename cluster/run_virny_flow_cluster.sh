#!/bin/bash

num_workers=$1

singularity exec --overlay /scratch/dh3553/virny_flow_project/vldb_sds_env.ext3:ro /scratch/work/public/singularity/ubuntu-20.04.1.sif /bin/bash

source /ext3/env.sh

# Start the task manager
python ../scripts/run_task_manager.py > ./task_manager.txt 2>&1 &

# Start worker processes
for i in {1..$num_workers}; do
    python ../scripts/run_worker.py > ./worker_$num_workers.txt 2>&1 &
done

# Wait for all background processes to finish
wait
