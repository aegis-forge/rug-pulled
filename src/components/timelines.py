import plotly.express as ex
import streamlit as st

from datetime import datetime
from math import ceil
from plotly.graph_objects import Figure, Scatter
from plotly.subplots import make_subplots
from random import randint
from streamlit.delta_generator import DeltaGenerator

from .paging import make_paging_component
from ..components.metrics import make_metrics_components
from ..helpers.compute import (
    compute_dependencies,
    compute_trend_category,
    compute_trend,
)
from ..models.neo import Workflow


ss = st.session_state
threshold = 0.1


def _make_plot_component(
    repo_name: str,
    workflow_name: str,
    workflow: Workflow,
    container: DeltaGenerator,
) -> None:
    trend = compute_trend(workflow, True)
    trend2 = compute_trend(workflow)
    trend_type = compute_trend_category(trend["tau"], trend["pvalue"], threshold)
    trend_type2 = compute_trend_category(trend2["tau"], trend2["pvalue"], threshold)

    workflow_plots = container.container(gap="small")
    workflow_name_container = workflow_plots.container(
        horizontal=True, vertical_alignment="center", gap="small"
    )

    _ = workflow_name_container.write(
        f"###### {workflow_name} _({len(workflow.commits)} commits)_"
    )
    _ = workflow_name_container.badge(
        label="Dep. Trend",
        icon=trend_type["type"],
        color=trend_type["color"]
        if trend_type["type"] == ":material/equal:"
        else "blue",
    )
    _ = workflow_name_container.badge(
        label="Vuln. Trend",
        icon=trend_type2["type"],
        color=trend_type2["color"],
    )
    _ = workflow_name_container.text(
        body="",
        help=f"**Deps**: τ = {trend['tau']}, p-value = {trend['pvalue']}\n\n"
        + f"**Vulns**: τ = {trend2['tau']}, p-value = {trend2['pvalue']}",
    )

    dependencies = compute_dependencies(workflow)
    plots_container = workflow_plots.container(horizontal=True)

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
            y=dependencies[ys[i] + "_vuln"],
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

    _ = plots_container.plotly_chart(
        figure_or_data=fig1,
        theme=None,
        key=f"{repo_name}-{workflow_name}-{randint(0, 100000)}",
        on_select="rerun",
    )
    _ = plots_container.plotly_chart(
        figure_or_data=fig2,
        theme=None,
        key=f"{repo_name}-{workflow_name}-{randint(0, 100000)}",
        on_select="rerun",
    )


def make_timelines_component() -> None:
    st.write("#### Plots")

    make_paging_component(
        ceil(len(ss["selected_workflows"]) / 5),
        "curr_page_timelines",
    )

    begin = (ss["curr_page_timelines"] - 1) * 5
    end = ss["curr_page_timelines"] * 5

    for repo_name in list(ss["selected_workflows"].keys())[begin:end]:
        workflows = ss["selected_workflows"][repo_name]

        st.write(f"##### {repo_name} _({len(workflows)} workflows)_")
        container = st.container(gap="medium")

        for workflow_name, workflow in workflows.items():
            _make_plot_component(repo_name, workflow_name, workflow, container)

    make_paging_component(
        ceil(len(ss["selected_workflows"]) / 5),
        "curr_page_timelines",
    )


def make_statistics_component() -> None:
    ss = st.session_state

    xs: list[datetime] = []
    ys: list[float] = []
    ys2: list[float] = []
    cs: list[str] = []
    hover: dict[str, list[str]] = {
        "repository": [],
        "workflow": [],
        "taus": [],
        "pvalues": [],
    }

    for repo_name, workflows in ss["selected_workflows"].items():
        for workflow_name, workflow in workflows.items():
            trend = compute_trend(workflow, True)
            trend2 = compute_trend(workflow)

            hover["repository"].append(repo_name)
            hover["workflow"].append(workflow_name)
            hover["taus"].append([trend["tau"], trend2["tau"]])
            hover["pvalues"].append([trend["pvalue"], trend2["pvalue"]])

            xs.append(len(workflow.commits))
            ys.append(trend["tau"])
            ys2.append(trend2["tau"])
            cs.append(
                f"pvalue deps <= {threshold} && pvalue vulns <= {threshold}"
                if trend["pvalue"] <= threshold and trend2["pvalue"] <= threshold
                else f"pvalue deps > {threshold} && pvalue vulns > {threshold}"
                if trend["pvalue"] > threshold and trend2["pvalue"] > threshold
                else f"pvalue deps > {threshold} || pvalue vulns > {threshold}"
            )

    # ----------------------

    trend_title_container = st.container(horizontal=True, gap="medium")
    trend_title_container.write("#### Vulnerability Trends")
    _ = trend_title_container.text(
        body="",
        help="Select a point on the plot to see the complete history for that workflow",
    )

    # ----------------------

    metrics_colors = ["green", "green", "gray", "red", "red"]
    metrics_labels = [
        ":material/keyboard_double_arrow_down:",
        ":material/keyboard_arrow_down:",
        ":material/equal:",
        ":material/keyboard_arrow_up:",
        ":material/keyboard_double_arrow_up:",
    ]

    computed_trend_types = [
        compute_trend_category(tau[1], pvalue[1], threshold)["type"]
        for tau, pvalue in zip(hover["taus"], hover["pvalues"])
    ]

    metrics_values: list[int] = [
        len(list(filter(lambda x: x == label, computed_trend_types)))
        for label in metrics_labels
    ]

    make_metrics_components(metrics_labels, metrics_values, metrics_colors)

    # ----------------------
    fig = make_subplots(rows=2, cols=1)

    fig = ex.scatter(
        x=ys,
        y=ys2,
        color=cs,
        hover_data=hover,
        color_discrete_map={
            f"pvalue deps <= {threshold} && pvalue vulns <= {threshold}": "blue",
            f"pvalue deps > {threshold} && pvalue vulns > {threshold}": "red",
            f"pvalue deps > {threshold} || pvalue vulns > {threshold}": "orange",
        },
    )

    _ = fig.update_yaxes(showgrid=False, zerolinecolor="#E6EAF1", range=[-1.1, 1.1])
    _ = fig.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1", range=[-1.1, 1.1])
    _ = fig.update_layout(
        xaxis_title="# dependencies trend τ",
        yaxis_title="# vulnerabilities trend τ",
    )

    trend_container = st.container()
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
