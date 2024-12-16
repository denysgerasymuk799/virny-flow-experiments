import pandas as pd
from duckdb import query as sqldf

from virny_flow.core.custom_classes.core_db_client import CoreDBClient
from virny_flow.visualizations.use_case_queries import get_best_pps_per_lp_and_run_num


def get_best_lps_for_exp_config(db_client: CoreDBClient, exp_config_name: str):
    best_pps_per_lp_and_run_num_df = get_best_pps_per_lp_and_run_num(db_client=db_client,
                                                                     exp_config_name=exp_config_name)
    print('best_pps_per_lp_and_run_num_df.shape:', best_pps_per_lp_and_run_num_df.shape)

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
