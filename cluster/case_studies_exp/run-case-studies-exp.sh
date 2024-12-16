# Define the list of tuples (exp_name, dataset, case_study, run_num, w1, w2, w3, exp_config_suffix, max_trials, email)
declare -a job_configs=(
    "case_studies_exp diabetes cs1 1 0.5 0.5 0.5 w_acc_0_5_w_fair_0_5_w_stab_0_5 200 dh3553"
)

# Initialize a counter
index=0

# Iterate through the array of job_configs
for job_config in "${job_configs[@]}"
do
    # Split the job_config into separate variables
    read -r exp_name dataset case_study run_num w1 w2 w3 exp_config_suffix max_trials email <<< "$job_config"
    template_file="../cluster/${exp_name}/virny-flow-${dataset}-${case_study}-template.sbatch"

    # Define the output file name
    output_file="../cluster/${exp_name}/sbatch_files/${exp_name}_${dataset}_${case_study}_w_${w1}_${w2}_${w3}_run_${run_num}_${index}.sbatch"

    # Create an empty file
    touch $output_file

    # Use sed to replace placeholders with actual values
    sed -e "s/<EXP_NAME>/${exp_name}/g" -e "s/<DATASET>/${dataset}/g" -e "s/<CASE_STUDY>/${case_study}/g" -e "s/<RUN_NUM>/${run_num}/g" -e "s/<W1>/${w1}/g" -e "s/<W2>/${w2}/g" -e "s/<W3>/${w3}/g" -e "s/<MAX_TRIALS>/${max_trials}/g" -e "s/<EXP_CONFIG_SUFFIX>/${exp_config_suffix}/g" -e "s/<EMAIL>/${email}/g" $template_file > $output_file

    # Execute a SLURM job
    sbatch $output_file

    echo "Job was executed: $output_file"

    # Increment the index
    ((index++))
done
