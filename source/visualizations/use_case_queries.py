import pandas as pd
from duckdb import query as sqldf

from virny.configs.constants import *
from virny_flow.core.custom_classes.core_db_client import CoreDBClient
from virny_flow.configs.constants import PHYSICAL_PIPELINE_OBSERVATIONS_TABLE, ALL_EXPERIMENT_METRICS_TABLE


DISPARITY_METRIC_METADATA = {
    EQUALIZED_ODDS_TPR: {"source_metric": TPR, "operation": "difference"},
    EQUALIZED_ODDS_TNR: {"source_metric": TNR, "operation": "difference"},
    EQUALIZED_ODDS_FPR: {"source_metric": FPR, "operation": "difference"},
    EQUALIZED_ODDS_FNR: {"source_metric": FNR, "operation": "difference"},
    ACCURACY_DIFFERENCE: {"source_metric": ACCURACY, "operation": "difference"},
    "Selection_Rate_Difference": {"source_metric": SELECTION_RATE, "operation": "difference"},
    DISPARATE_IMPACT: {"source_metric": SELECTION_RATE, "operation": "ratio"},
    LABEL_STABILITY_RATIO: {"source_metric": LABEL_STABILITY, "operation": "ratio"},
    LABEL_STABILITY_DIFFERENCE: {"source_metric": LABEL_STABILITY, "operation": "difference"},
    JITTER_DIFFERENCE: {"source_metric": JITTER, "operation": "difference"},
    IQR_DIFFERENCE: {"source_metric": IQR, "operation": "difference"},
    STD_DIFFERENCE: {"source_metric": STD, "operation": "difference"},
    STD_RATIO: {"source_metric": STD, "operation": "ratio"},
    OVERALL_UNCERTAINTY_DIFFERENCE: {"source_metric": OVERALL_UNCERTAINTY, "operation": "difference"},
    OVERALL_UNCERTAINTY_RATIO: {"source_metric": OVERALL_UNCERTAINTY, "operation": "ratio"},
    ALEATORIC_UNCERTAINTY_DIFFERENCE: {"source_metric": ALEATORIC_UNCERTAINTY, "operation": "difference"},
    ALEATORIC_UNCERTAINTY_RATIO: {"source_metric": ALEATORIC_UNCERTAINTY, "operation": "ratio"},
    EPISTEMIC_UNCERTAINTY_DIFFERENCE: {"source_metric": EPISTEMIC_UNCERTAINTY, "operation": "difference"},
    EPISTEMIC_UNCERTAINTY_RATIO: {"source_metric": EPISTEMIC_UNCERTAINTY, "operation": "ratio"},
}



def get_best_pps_per_lp_and_run_num(db_client: CoreDBClient, exp_config_name: str):
    pipeline = [
        # Step 1: Filter documents in PHYSICAL_PIPELINE_OBSERVATIONS_TABLE with the defined exp_config_name
        {
            "$match": {
                "exp_config_name": exp_config_name,
                "deletion_flag": False
            }
        },
        # Step 2: Group to get the maximum `compound_pp_quality` per `exp_config_name`, `logical_pipeline_uuid`, and `run_num`
        {
            "$group": {
                "_id": {
                    "exp_config_name": "$exp_config_name",
                    "run_num": "$run_num",
                    "logical_pipeline_uuid": "$logical_pipeline_uuid",
                },
                "max_compound_pp_quality": { "$max": "$compound_pp_quality" },
                "best_pipeline_doc": {
                    "$first": {
                        "physical_pipeline_uuid": "$physical_pipeline_uuid",
                        "run_num": "$run_num",
                        "compound_pp_quality": "$compound_pp_quality"
                    }
                }
            }
        },
        # Step 3: Replace root with the captured document
        {
            "$replaceRoot": {
                "newRoot": {
                    "exp_config_name": "$_id.exp_config_name",
                    "logical_pipeline_uuid": "$_id.logical_pipeline_uuid",
                    "physical_pipeline_uuid": "$best_pipeline_doc.physical_pipeline_uuid",
                    "run_num": "$best_pipeline_doc.run_num",
                    "compound_pp_quality": "$best_pipeline_doc.compound_pp_quality"
                }
            }
        },
        # Step 4: Join with `all_experiment_metrics` based on `physical_pipeline_uuid`
        {
            "$lookup": {
                "from": ALL_EXPERIMENT_METRICS_TABLE,
                "let": { "physical_uuid": "$physical_pipeline_uuid", "physical_run_num": "$run_num" },
                "pipeline": [
                    { "$match": {
                        "$expr": {
                            "$and": [
                                { "$eq": ["$exp_config_name", exp_config_name] },
                                { "$eq": ["$run_num", "$$physical_run_num"] },
                                { "$eq": ["$physical_pipeline_uuid", "$$physical_uuid"] },
                            ]
                        }
                    }}
                ],
                "as": "experiment_metrics"
            }
        },
        # Step 5: Unwind to get one document per metric in `all_experiment_metrics`
        {
            "$unwind": "$experiment_metrics"
        },
        # Step 6: Project only the fields you need (optional)
        {
            "$project": {
                "_id": 0,
                "exp_config_name": 1,
                "run_num": 1,
                "logical_pipeline_uuid": 1,
                "physical_pipeline_uuid": 1,
                "compound_pp_quality": 1,
                "experiment_metrics.logical_pipeline_name": 1,
                "experiment_metrics.dataset_name": 1,
                "experiment_metrics.null_imputer_name": 1,
                "experiment_metrics.fairness_intervention_name": 1,
                "experiment_metrics.model_name": 1,
                "experiment_metrics.subgroup": 1,
                "experiment_metrics.metric": 1,
                "experiment_metrics.metric_value": 1,
                "experiment_metrics.runtime_in_mins": 1,
            }
        }
    ]

    # Run the aggregation pipeline
    results = list(db_client.client[db_client.db_name][PHYSICAL_PIPELINE_OBSERVATIONS_TABLE].aggregate(pipeline))

    # Convert results to a pandas DataFrame
    all_metrics_df = pd.json_normalize(results)
    all_metrics_df.columns = [col.replace("experiment_metrics.", "") for col in all_metrics_df.columns]

    # Create columns based on values in the Subgroup column
    pivoted_all_metrics_df = all_metrics_df.pivot(columns='subgroup', values='metric_value',
                                                  index=[col for col in all_metrics_df.columns
                                                         if col not in ('subgroup', 'metric_value')]).reset_index()

    return pivoted_all_metrics_df


def get_best_lps_for_exp_config(db_client: CoreDBClient, exp_config_name: str):
    best_pps_per_lp_and_run_num_df = get_best_pps_per_lp_and_run_num(db_client=db_client,
                                                                     exp_config_name=exp_config_name)

    # Get best lp for the specific exp_config_name
    max_lp_avg_compound_pp_quality = sqldf("""
        SELECT MAX(avg_compound_pp_quality) AS max_lp_avg_compound_pp_quality
        FROM (
            SELECT logical_pipeline_uuid, AVG(compound_pp_quality) as avg_compound_pp_quality
            FROM best_pps_per_lp_and_run_num_df
            GROUP BY logical_pipeline_uuid
        ) AS avg_tbl
    """).to_df().iloc[0, 0]
    print('max_lp_avg_compound_pp_quality:', max_lp_avg_compound_pp_quality)

    best_logical_pipeline_uuid = sqldf(f"""
        SELECT logical_pipeline_uuid
        FROM (
            SELECT logical_pipeline_uuid, AVG(compound_pp_quality) AS avg_compound_pp_quality
            FROM best_pps_per_lp_and_run_num_df
            GROUP BY logical_pipeline_uuid
        ) AS avg_tbl
        WHERE avg_compound_pp_quality = {max_lp_avg_compound_pp_quality}
    """).to_df().iloc[0, 0]
    print('best_logical_pipeline_uuid:', best_logical_pipeline_uuid)

    return best_pps_per_lp_and_run_num_df[best_pps_per_lp_and_run_num_df['logical_pipeline_uuid'] == best_logical_pipeline_uuid]


def get_best_lps_per_exp_config(secrets_path: str, exp_config_names: list):
    db_client = CoreDBClient(secrets_path)
    db_client.connect()

    best_lp_metrics_per_exp_config_df = pd.DataFrame()
    for exp_config_name in exp_config_names:
        print(f'Extracting metrics for {exp_config_name}...')
        best_lp_metrics_df = get_best_lps_for_exp_config(db_client=db_client, exp_config_name=exp_config_name)
        best_lp_metrics_per_exp_config_df = pd.concat([best_lp_metrics_per_exp_config_df, best_lp_metrics_df])
        print(f'Extracted metrics for {exp_config_name}\n')

    db_client.close()

    return best_lp_metrics_per_exp_config_df


def get_models_disparity_metric_df(subgroup_metrics_df: pd.DataFrame, disparity_metric_name: str, group: str):
    source_metric, operation = (DISPARITY_METRIC_METADATA[disparity_metric_name]["source_metric"],
                                DISPARITY_METRIC_METADATA[disparity_metric_name]["operation"])
    group_metrics_df = subgroup_metrics_df[subgroup_metrics_df['metric'] == source_metric]
    if operation == "ratio":
        group_metrics_df['disparity_metric_value'] = group_metrics_df[group + '_dis'] / group_metrics_df[group + '_priv']
    else:
        group_metrics_df['disparity_metric_value'] = group_metrics_df[group + '_dis'] - group_metrics_df[group + '_priv']

    group_metrics_df['metric'] = disparity_metric_name
    return group_metrics_df
