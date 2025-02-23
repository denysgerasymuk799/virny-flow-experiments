import os
import json
from openbox import History
from datetime import datetime
from ConfigSpace import ConfigurationSpace
from openbox.utils.history import Observation

from virny_flow.configs.structs import BOAdvisorConfig
from virny_flow.visualizations.viz_utils import build_visualizer, create_config_space


def load_history(filename: str, config_space: ConfigurationSpace, defined_objectives: list) -> 'History':
    if not os.path.exists(filename):
        raise FileNotFoundError(f'File not found: {filename}')
    with open(filename, 'r') as f:
        data = json.load(f)

    # Get original losses from weighted losses
    for obs in data["observations"]:
        obs["objectives"] = [obs["objectives"][0] / defined_objectives[0]['weight'],
                             obs["objectives"][1] / defined_objectives[1]['weight']]

    global_start_time = data.pop('global_start_time')
    global_start_time = datetime.fromisoformat(global_start_time)
    observations = data.pop('observations')
    observations = [Observation.from_dict(obs, config_space) for obs in observations]

    history = History(**data)
    history.global_start_time = global_start_time
    history.update_observations(observations)

    return history


if __name__ == '__main__':
    # Input variables
    exp_config_name = 'case_studies_exp_diabetes_cs2_w_acc_0_5_w_stab_0_5'
    run_num = 1
    lp_name = 'None&NO_FAIRNESS_INTERVENTION&rf_clf'
    history_filename = 'history_2024-12-17-08-16-55-433005.json'
    max_trials = 200

    defined_objectives = [
        { "name": "objective_1", "metric": "F1", "group": "overall", "weight": 0.5 },
        # { "name": "objective_2", "metric": "Equalized_Odds_TPR", "group": "Gender", "weight": 0.25 },
        { "name": "objective_2", "metric": "Label_Stability", "group": "overall", "weight": 0.5 }
    ]
    surrogate_model_type = 'gp'  # 'gp' or 'prf'
    bo_advisor_config = BOAdvisorConfig()

    config_space = create_config_space(lp_name)
    history_path = f'../logs/history/{exp_config_name}/run_num_{str(run_num)}/{lp_name}/' + history_filename
    history = load_history(history_path, config_space, defined_objectives)

    task_info = {
        'advisor_type': 'default',
        'max_runs': max_trials,
        'max_runtime_per_trial': bo_advisor_config.max_runtime_per_trial,
        'surrogate_type': surrogate_model_type,
        'constraint_surrogate_type': None,
        'transfer_learning_history': bo_advisor_config.transfer_learning_history,
    }

    visualizer = build_visualizer(
        task_info=task_info,
        option='advanced',
        history=history,
        auto_open_html=True,
    )
    visualizer.setup()
    visualizer.update()
