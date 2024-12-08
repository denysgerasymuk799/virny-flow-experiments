#!/bin/bash

# EXECUTE THIS SCRIPT FROM virny-flow-experiments/logs DIRECTORY

# ====================================================================================
# Define SLURM configs
# ====================================================================================
#SBATCH --nodes=1
#SBATCH --mem=16GB
#SBATCH --cpus-per-task=12
#SBATCH --time=48:00:00
#SBATCH --mail-type=END
#SBATCH --mail-user=dh3553@nyu.edu
#SBATCH --account=pr_152_general
#SBATCH --job-name=german_experiments7
#SBATCH --output=%j_german_experiments7.out

module purge


# ====================================================================================
# Default parameters
# ====================================================================================
EXP_CONFIG_NAME=german_experiments7
NUM_WORKERS=3
CLUSTER_TYPE=one_node_configs  # one_node_configs or many_node_configs
EMAIL=dh3553
SESSION=${SLURM_JOB_ID}_${EXP_CONFIG_NAME}


# ====================================================================================
# Define exp_config.yaml
# ====================================================================================
mkdir ./$SESSION
mkdir -p ./$SESSION/tmp/zookeeper-data/
mkdir -p ./$SESSION/tmp/zookeeper-logs/
mkdir -p ./$SESSION/tmp/kafka-logs/

cat <<EOL > ./$SESSION/exp_config.yaml
# General experiment parameters
exp_config_name: "$EXP_CONFIG_NAME"
dataset: "german"
sensitive_attrs_for_intervention: ["sex"]
null_imputers: ["miss_forest"]
fairness_interventions: ["DIR"]
models: ["dt_clf"]
run_nums: [1, 2]
secrets_path: "/home/$EMAIL/projects/virny-flow-experiments/scripts/configs/secrets.env"

# Parameters for optimisation
ref_point: [0.20, 0.10]
objectives:
  - { name: "objective_1", metric: "F1", group: "overall", weight: 0.5 }
  - { name: "objective_2", metric: "Equalized_Odds_TPR", group: "sex", weight: 0.5 }
max_trials: 3
num_workers: $NUM_WORKERS
num_pp_candidates: 2
training_set_fractions_for_halting: [0.5, 0.75, 1.0]
exploration_factor: 0.5
risk_factor: 0.5
EOL


# ====================================================================================
# Start VirnyFlow cluster
# ====================================================================================
# Start Kafka
bash ../cluster/$CLUSTER_TYPE/run_singularity_kafka.sh $NUM_WORKERS $SESSION

# Start virny_flow_cluster
singularity exec \
	    --overlay /scratch/$EMAIL/virny_flow_project/vldb_sds_env.ext3:ro \
	    /scratch/work/public/singularity/ubuntu-20.04.1.sif \
	    /bin/bash -c "source /ext3/env.sh; bash ../cluster/$CLUSTER_TYPE/run_virny_flow_cluster.sh $NUM_WORKERS $SESSION $EMAIL"
