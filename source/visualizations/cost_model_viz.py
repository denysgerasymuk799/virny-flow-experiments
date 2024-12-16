import pandas as pd
import altair as alt
from altair.utils.schemapi import Undefined

from virny_flow.visualizations.use_case_queries import get_models_disparity_metric_df


def create_box_plot_per_cost_model(to_plot: pd.DataFrame, metric_name: str, group: str = 'overall',
                                   base_font_size: int = 22, ylim=Undefined):
    """
    Creates an Altair box plot for the specified metric from the given DataFrame.

    """
    to_plot['exp_config_name'] = to_plot['exp_config_name'].str.replace('cost_model_exp1_folk_emp_', '', regex=False)
    to_plot['exp_config_name'] = to_plot['exp_config_name'].str.replace('w_', '', regex=False)

    if group == 'overall':
        # Filter the DataFrame for the specified metric
        if metric_name in ('runtime_in_mins', 'compound_pp_quality'):
            filtered_df = to_plot[to_plot["metric"] == "F1"]
            y_column = metric_name
            title = "Runtime in Mins" if metric_name == "runtime_in_mins" else "Compound PP Quality"
        else:
            filtered_df = to_plot[to_plot["metric"] == metric_name]
            y_column = 'overall'
            title = metric_name
    else:
        filtered_df = get_models_disparity_metric_df(subgroup_metrics_df=to_plot,
                                                     disparity_metric_name=metric_name,
                                                     group=group)
        y_column = 'disparity_metric_value'

    # Create the box plot
    box_plot = alt.Chart(filtered_df).mark_boxplot(
        ticks=True,
        median={'stroke': 'black', 'strokeWidth': 0.7},
    ).encode(
        x=alt.X('exp_config_name:N', title=None, axis=alt.Axis(labelAngle=-45, labelLimit=300)),
        y=alt.Y(f'{y_column}:Q', title=title, scale=alt.Scale(zero=False, domain=ylim)),
    ).properties(
        width=400,
        height=400
    )

    final_chart = (
        box_plot.configure_view(
            stroke=None
        ).configure_axis(
            labelFontSize=base_font_size,
            titleFontSize=base_font_size + 6,
            labelFontWeight='normal',
            titleFontWeight='normal',
        ).configure_title(
            fontSize=base_font_size + 6,
        )
    )

    return final_chart
