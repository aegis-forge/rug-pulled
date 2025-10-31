import plotly.express as ex
import streamlit as st

from datetime import datetime
from math import ceil
from plotly.graph_objects import Figure
from streamlit.delta_generator import DeltaGenerator

from .paging import make_paging_component
from ..models.neo import Workflow
from ..helpers.compute import compute_dependencies, compute_trend_category, compute_trend


ss = st.session_state
threshold = 0.5


def _make_plot_component(repo_name: str, workflow_name: str, workflow: Workflow, container: DeltaGenerator) -> None:    
    trend = compute_trend(workflow)
    trend_type = compute_trend_category(trend["tau"], trend["pvalue"], threshold)
    
    workflow_plots = container.container(gap="small")
    workflow_name_container = workflow_plots.container(
        horizontal=True,
        vertical_alignment="center",
        gap="small"
    )
    
    _ = workflow_name_container.write(
        f"###### {workflow_name} _({len(workflow.commits)} commits)_"
    )
    _ = workflow_name_container.badge(
        label="Vuln. Trend",
        icon=trend_type["type"],
        color=trend_type["color"],
    )
    _ = workflow_name_container.text(
        body="",
        help=f"τ = {trend["tau"]}, p-value = {trend["pvalue"]}"
    )
    
    dependencies = compute_dependencies(workflow)
    col1, col2 = workflow_plots.columns(2)

    fig1 = Figure()
    fig2 = Figure()
    
    ys = ["direct", "direct_dev", "direct_opt", "indirect"]
    colors = [
        "rgb(99,110,251)",
        "rgb(110, 251, 99)",
        "rgb(250, 164, 97)",
        "rgb(61, 58, 42)",
    ]

    for i in range(len(ys)):
        fig1 = fig1.add_scatter(
            x=dependencies["dates"],
            y=dependencies[ys[i]],
            name=ys[i],
            marker={"color": colors[i]},
            line_shape="hv",
            mode="lines+markers",
        )
        
        fig2 = fig2.add_scatter(
            x=dependencies["dates"],
            y=dependencies[ys[i]+"_vuln"],
            name=ys[i],
            marker={"color": colors[i]},
            line_shape="hv",
            mode="lines+markers",
        )
        
    fig1 = fig1.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1")
    fig1 = fig1.update_yaxes(showgrid=True, zerolinecolor="#E6EAF1")
    fig1 = fig1.update_layout(hovermode="x unified")
    
    fig2 = fig2.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1")
    fig2 = fig2.update_yaxes(showgrid=True, zerolinecolor="#E6EAF1")
    fig2 = fig2.update_layout(hovermode="x unified")

    _ = col1.plotly_chart(
        figure_or_data=fig1,
        theme=None,
        key=f"{repo_name}-{workflow}-acol1",
        on_select="rerun"
    )
    _ = col2.plotly_chart(
        figure_or_data=fig2,
        theme=None,
        key=f"{repo_name}-{workflow}-acol2",
        on_select="rerun"
    )


def make_timelines_component() -> None:
    st.write("#### Plots")
    
    make_paging_component(ceil(len(ss["selected_workflows"]) / 5))

    begin = (ss["curr_page_timelines"] - 1) * 5 + 1
    end = ss["curr_page_timelines"] * 5 + 1

    for repo_name in list(ss["selected_workflows"].keys())[begin:end]:
        workflows = ss["selected_workflows"][repo_name]

        st.write(f"##### {repo_name} _({len(workflows)} workflows)_")
        container = st.container(gap="medium")
        
        for workflow_name, workflow in workflows.items():
            _make_plot_component(repo_name, workflow_name, workflow, container)

    make_paging_component(ceil(len(ss["selected_workflows"]) / 5))


def make_statistics_component() -> None:
    ss = st.session_state

    xs: list[datetime] = []
    ys: list[float] = []
    cs: list[str] = []
    hover: dict[str, list[str]] = {
        "repository": [],
        "workflow": [],
        "tau": [],
        "pvalue": [],
    }

    for repo_name, workflows in ss["selected_workflows"].items():
        for workflow_name, workflow in workflows.items():
            trend = compute_trend(workflow)

            hover["repository"].append(repo_name)
            hover["workflow"].append(workflow_name)
            hover["tau"].append(trend["tau"])
            hover["pvalue"].append(trend["pvalue"])

            xs.append(len(workflow.commits))
            ys.append(trend["tau"])
            cs.append(
                f"pvalue <= {threshold}"
                if trend["pvalue"] <= threshold
                else f"pvalue > {threshold}"
            )

    # ----------------------
    
    trend_title_container = st.container(horizontal=True, gap="medium")
    trend_title_container.write("#### Vulnerability Trends")
    _ = trend_title_container.text(
        body="",
        help="Select a point on the plot to see the complete history for that workflow",
    )
    
    # ----------------------

    trend_colors = ["green", "green", "gray", "red", "red"]
    trend_types = [
        ":material/keyboard_double_arrow_down:",
        ":material/keyboard_arrow_down:",
        ":material/equal:",
        ":material/keyboard_arrow_up:",
        ":material/keyboard_double_arrow_up:",
    ]

    computed_trend_types = [
        compute_trend_category(tau, pvalue, threshold)["type"]
        for tau, pvalue in zip(hover["tau"], hover["pvalue"])
    ]

    trends_metrics_container = st.container(
        horizontal=True,
        vertical_alignment="center",
        horizontal_alignment="left",
        gap="large",
    )

    for trend_type, color in zip(trend_types, trend_colors):
        trends_metrics_container.metric(
            label=f"**:{color}[{trend_type}]**",
            value=len(list(filter(lambda x: x == trend_type, computed_trend_types))),
            width="content",
        )

    # ----------------------

    fig = ex.scatter(x=xs, y=ys, color=cs, hover_data=hover)

    _ = fig.update_yaxes(showgrid=False, zerolinecolor="#E6EAF1", range=[-1.1, 1.1])
    _ = fig.update_xaxes(
        showgrid=False, zerolinecolor="#E6EAF1", range=[0.5, max(xs) + 2]
    )
    _ = fig.update_layout(yaxis_title="value of τ", xaxis_title="# of commits")

    trend_container = st.container(horizontal=True)
    selected_workflow = trend_container.plotly_chart(
        figure_or_data=fig,
        theme=None,
        on_select="rerun",
        selection_mode="points",
    )
    
    if len(selected_workflow["selection"]["points"]) == 1:
        repo_name = selected_workflow["selection"]["points"][0]["customdata"][0]
        workflow_name = selected_workflow["selection"]["points"][0]["customdata"][1]
        
        _make_plot_component(
            repo_name,
            workflow_name,
            ss["selected_workflows"][repo_name][workflow_name],
            trend_container,
        )
