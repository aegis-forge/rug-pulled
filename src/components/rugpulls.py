from math import ceil

import plotly.express as ex
import streamlit as st
from numpy import mean, median, where
from pandas import DataFrame

from ..components.metrics import make_metrics_components
from ..components.paging import make_paging_component
from ..helpers.compute import compute_rug_pulls


def _make_rug_pulls_metrics(rug_pulls: DataFrame) -> None:
    fixed = rug_pulls[rug_pulls["fix_category"] == "fixed"]
    not_fixed = rug_pulls[rug_pulls["fix_category"] != "fixed"]
    fixable = not_fixed[not_fixed["fix_category"] == "fixable"]
    fixable_deps = not_fixed[not_fixed["fix_category"] == "dep_fixable"]
    not_fixable = not_fixed[not_fixed["fix_category"] == "unfixable"]

    workflows = [
        len(workflows) for workflows in st.session_state["selected_workflows"].values()
    ]
    commits = [
        len(workflows) for workflows in st.session_state["selected_commits"].values()
    ]

    make_metrics_components(
        labels=[
            "# Repositories",
            "# Workflows",
            "Min. per Repo",
            "Max. per Repo",
            "Avg. per Repo",
            "Med. per Repo",
            "# Commits",
            "Min. per Workflow",
            "Max. per Workflow",
            "Avg. per Workflow",
            "Med. per Workflow",
        ],
        values=[
            len(st.session_state["selected_workflows"]),
            sum(workflows),
            min(workflows),
            max(workflows),
            round(mean(workflows), 2),
            int(median(workflows)),
            sum(commits),
            min(commits),
            max(commits),
            round(mean(commits), 2),
            int(median(commits)),
        ],
    )   

    per_repo = rug_pulls.groupby(by=["repo"]).size()
    per_workflow = rug_pulls.groupby(by=["repo", "workflow"]).size()
    per_commit = rug_pulls.groupby(by=["repo", "workflow", "hash"]).size()
    print(per_commit)

    make_metrics_components(
        labels=[
            "# Rug-Pulls",
            "Min. per Commit",
            "Max. per Commit",
            "Avg. per Commit",
            "Min. per Workflow",
            "Max. per Workflow",
            "Avg. per Workflow",
            "Min. per Repo",
            "Max. per Repo",
            "Avg. per Repo",
        ],
        values=[
            len(rug_pulls),
            per_commit.min(),
            per_commit.max(),
            round(per_commit.mean(), 2),
            per_workflow.min(),
            per_workflow.max(),
            round(per_workflow.mean(), 2),
            per_repo.min(),
            per_repo.max(),
            round(per_repo.mean(), 2),
        ],
    )

    make_metrics_components(
        labels=[
            "# RP Repositories",
            "# RP Workflows",
            "# RP Commits",
            "# RP Actions",
            "# RP Action Versions",
        ],
        values=[
            len(rug_pulls.groupby(["repo"])),
            len(rug_pulls.groupby(["repo", "workflow"])),
            len(rug_pulls.groupby(["repo", "workflow", "hash"])),
            len(rug_pulls.groupby(["action"])),
            len(rug_pulls.groupby(["action", "version"])),
        ],
    )

    make_metrics_components(
        labels=[
            "# Fixed",
            "% Fixed",
            "MTTF (days)",
            "Min. TTF (days)",
            "Max. TTF (days)",
            "Med. TTF (days)",
        ],
        values=[
            len(fixed),
            round(len(fixed) * 100 / len(rug_pulls), 2),
            round(fixed["ttf"].mean(), 2) if len(fixed["ttf"]) > 0 else 0,
            int(fixed["ttf"].min()) if len(fixed["ttf"]) > 0 else 0,
            int(fixed["ttf"].max()) if len(fixed["ttf"]) > 0 else 0,
            int(fixed["ttf"].median()) if len(fixed["ttf"]) > 0 else 0,
        ],
        colors=["green", "green", "", "", "", ""],
    )

    workflow_maint = fixed[fixed["fix_actor"] == "Workflow"]
    action_maint = fixed[fixed["fix_actor"] == "Action"]

    make_metrics_components(
        labels=[
            "# By Workflow Maint.",
            "% By Workflow Maint.",
            "MTTF (days)",
            "Min. TTF (days)",
            "Max. TTF (days)",
            "Med. TTF (days)",
        ],
        values=[
            len(workflow_maint),
            round(len(workflow_maint) * 100 / len(rug_pulls), 2),
            int(workflow_maint["ttf"].mean()) if len(workflow_maint["ttf"]) > 0 else 0,
            int(workflow_maint["ttf"].min()) if len(workflow_maint["ttf"]) > 0 else 0,
            int(workflow_maint["ttf"].max()) if len(workflow_maint["ttf"]) > 0 else 0,
            int(workflow_maint["ttf"].median()),
        ],
        colors=["green", "green", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# By Action Maint.",
            "% By Action Maint.",
            "MTTF (days)",
            "Min. TTF (days)",
            "Max. TTF (days)",
            "Med. TTF (days)",
        ],
        values=[
            len(action_maint),
            round(len(action_maint) * 100 / len(rug_pulls), 2),
            round(action_maint["ttf"].mean(), 2) if len(action_maint["ttf"]) > 0 else 0,
            int(action_maint["ttf"].min()) if len(action_maint["ttf"]) > 0 else 0,
            int(action_maint["ttf"].max()) if len(action_maint["ttf"]) > 0 else 0,
            int(action_maint["ttf"].median()) if len(action_maint["ttf"]) > 0 else 0,
        ],
        colors=["green", "green", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# Not Fixed",
            "% Not Fixed",
            "MOVA (days)",
            "Min. OVA (days)",
            "Max. OVA (days)",
            "Med. OVA (days)",
        ],
        values=[
            len(not_fixed),
            round(len(not_fixed) * 100 / len(rug_pulls), 2),
            round(not_fixed["elapsed"].dropna().mean(), 2)
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            int(not_fixed["elapsed"].dropna().min())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            int(not_fixed["elapsed"].dropna().max())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            int(not_fixed["elapsed"].dropna().median())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
        ],
        colors=["red", "red", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# Fixable",
            "% Fixable",
            "MOVA (days)",
            "MTTPF (days)",
            "Min. OVA (days)",
            "Min. TTPF (days)",
            "Max. OVA (days)",
            "Max. TTPF (days)",
            "Med. OVA (days)",
            "Med. TTPF (days)",
        ],
        values=[
            len(fixable),
            round(len(fixable) * 100 / len(rug_pulls), 2),
            round(fixable["elapsed"].dropna().mean(), 2)
            if len(fixable["elapsed"].dropna()) > 0
            else 0,
            round(fixable["ttpf"].mean(), 2) if len(fixable["ttpf"]) > 0 else 0,
            int(fixable["elapsed"].min()) if len(fixable["elapsed"]) > 0 else 0,
            int(fixable["ttpf"].min()) if len(fixable["ttpf"]) > 0 else 0,
            int(fixable["elapsed"].max()) if len(fixable["elapsed"]) > 0 else 0,
            int(fixable["ttpf"].max()) if len(fixable["ttpf"]) > 0 else 0,
            int(fixable["elapsed"].median()) if len(fixable["elapsed"]) > 0 else 0,
            int(fixable["ttpf"].median()) if len(fixable["ttpf"]) > 0 else 0,
        ],
        colors=["orange", "orange", "", "", "", "", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# Fixable Deps.",
            "% Fixable Deps.",
            "MOVA (days)",
            "Min. OVA (days)",
            "Max. OVA (days)",
            "Med. OVA (days)",
        ],
        values=[
            len(fixable_deps),
            round(len(fixable_deps) * 100 / len(rug_pulls), 2),
            round(fixable_deps["elapsed"].dropna().mean(), 2)
            if len(fixable_deps["elapsed"].dropna()) > 0
            else 0,
            int(fixable_deps["elapsed"].dropna().min())
            if len(fixable_deps["elapsed"].dropna()) > 0
            else 0,
            int(fixable_deps["elapsed"].dropna().max())
            if len(fixable_deps["elapsed"].dropna()) > 0
            else 0,
            int(fixable_deps["elapsed"].dropna().median())
            if len(fixable_deps["elapsed"].dropna()) > 0
            else 0,
        ],
        colors=["orange", "orange", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# Not Fixable",
            "% Not Fixable",
            "MOVA (days)",
            "Min. OVA (days)",
            "Max. OVA (days)",
            "Med. OVA (days)",
        ],
        values=[
            len(not_fixable),
            round(len(not_fixable) * 100 / len(rug_pulls), 2),
            round(not_fixable["elapsed"].dropna().mean(), 2)
            if len(not_fixable["elapsed"].dropna()) > 0
            else 0,
            int(not_fixable["elapsed"].dropna().min())
            if len(not_fixable["elapsed"].dropna()) > 0
            else 0,
            int(not_fixable["elapsed"].dropna().max())
            if len(not_fixable["elapsed"].dropna()) > 0
            else 0,
            int(not_fixable["elapsed"].dropna().median())
            if len(not_fixable["elapsed"].dropna()) > 0
            else 0,
        ],
        colors=["gray", "gray", "", "", "", ""],
    )


def make_rug_pulls_component() -> None:
    rug_pulled_workflows_title = st.container(
        horizontal=True,
        vertical_alignment="center",
    )
    rug_pulled_workflows_title.write("#### Rug-Pulled Actions")
    _ = rug_pulled_workflows_title.text(
        body="",
        help="Rug-pulled workflow commits are those commits where the maintainers of"
        + " the used Actions upgrade/downgrade their versions. By doing so, they introduce"
        + " vulnerabilities in the workflow. Workflow maintainers do not introduce these"
        + " vulnerabilities directly.",
    )

    st.write("##### Statistics")

    rug_pulls = compute_rug_pulls()
    fixed_df = rug_pulls[rug_pulls["fix_category"] == "fixed"]
    not_fixed_df = rug_pulls[rug_pulls["fix_category"] != "fixed"]
    fixable_df = not_fixed_df[not_fixed_df["fix_category"] == "fixable"]
    fixable_deps_df = not_fixed_df[not_fixed_df["fix_category"] == "dep_fixable"]
    non_fixable_df = rug_pulls[rug_pulls["fix_category"] == "unfixable"]

    _make_rug_pulls_metrics(rug_pulls)

    # ===========================

    st.write("##### Plots")

    cols_o = st.columns(3)
    cols_o[0].plotly_chart(
        ex.scatter(
            fixed_df.sort_values(by="date"),
            x="date",
            y="ttf",
            color="fix_actor",
            title="TTF (overall)",
            color_discrete_map={"Workflow": "blue", "Action": "lightblue"},
        )
    )
    cols_o[1].plotly_chart(
        ex.scatter(
            not_fixed_df.sort_values(by="date"),
            x="date",
            y="elapsed",
            title="OVA (overall)",
            labels={"elapsed": "ova"},
            color="fix_category",
            color_discrete_map={
                "dep_fixable": "red",
                "fixable": "orange",
                "unfixable": "gray",
            },
        )
    )
    cols_o[2].plotly_chart(
        ex.scatter(
            not_fixed_df[not_fixed_df["fix_category"] != "unfixable"].sort_values(
                by="date"
            ),
            x="date",
            y="ttpf",
            title="TTPF (overall)",
            color="fix_category",
            color_discrete_map={
                "dep_fixable": "red",
                "fixable": "orange",
            },
        )
    )

    cols_s = st.columns(3)
    cols_s[0].plotly_chart(
        ex.scatter(
            fixed_df[fixed_df["fix_actor"] == "Workflow"].sort_values(by="date"),
            x="date",
            y="ttf",
            title="TTF (by workflow maint.)",
            color_discrete_sequence=["blue"],
        )
    )
    cols_s[1].plotly_chart(
        ex.scatter(
            fixable_df.sort_values(by="date"),
            x="date",
            y="elapsed",
            title="OVA (fixable)",
            labels={"elapsed": "ova"},
            color_discrete_sequence=["orange"],
        )
    )
    cols_s[2].plotly_chart(
        ex.scatter(
            fixable_df.sort_values(by="date"),
            x="date",
            y="ttpf",
            title="TTPF (fixable)",
            color_discrete_sequence=["orange"],
        )
    )

    cols_s_2 = st.columns(3)
    cols_s_2[0].plotly_chart(
        ex.scatter(
            fixed_df[fixed_df["fix_actor"] == "Action"].sort_values(by="date"),
            x="date",
            y="ttf",
            title="TTF (by action maint.)",
            color_discrete_sequence=["lightblue"],
        )
    )
    cols_s_2[1].plotly_chart(
        ex.scatter(
            fixable_deps_df.sort_values(by="date"),
            x="date",
            y="elapsed",
            title="OVA (fixable deps.)",
            labels={"elapsed": "ova"},
            color_discrete_sequence=["red"],
        )
    )
    cols_s_2[2].plotly_chart(
        ex.scatter(
            fixable_deps_df.sort_values(by="date"),
            x="date",
            y="ttpf",
            title="TTPF (fixable deps.)",
            color_discrete_sequence=["red"],
        )
    )

    cols_s_3 = st.columns(3)
    cols_s_3[0].empty()
    cols_s_3[1].plotly_chart(
        ex.scatter(
            non_fixable_df.sort_values(by="date"),
            x="date",
            y="elapsed",
            title="OVA (unfixable)",
            labels={"elapsed": "ova"},
            color_discrete_sequence=["gray"],
        )
    )
    cols_s_3[2].empty()

    # ===========================

    min_hist = min(
        fixed_df["ttf"].dropna().min(),
        not_fixed_df["elapsed"].dropna().min(),
        not_fixed_df[not_fixed_df["fix_category"] != "unfixable"]["ttpf"]
        .dropna()
        .min(),
    )
    max_hist = max(
        fixed_df["ttf"].dropna().max(),
        not_fixed_df["elapsed"].dropna().max(),
        not_fixed_df[not_fixed_df["fix_category"] != "unfixable"]["ttpf"]
        .dropna()
        .max(),
    )

    cols_o2 = st.columns(3)
    cols_o2[0].plotly_chart(
        ex.histogram(
            fixed_df.sort_values(by="date"),
            x="ttf",
            color="fix_actor",
            title="TTF (overall)",
            nbins=100,
            color_discrete_map={"Workflow": "blue", "Action": "lightblue"},
        )
    )
    cols_o2[1].plotly_chart(
        ex.histogram(
            not_fixed_df.sort_values(by="date"),
            x="elapsed",
            title="OVA (overall)",
            labels={"elapsed": "ova"},
            color="fix_category",
            nbins=100,
            color_discrete_map={
                "dep_fixable": "red",
                "fixable": "orange",
                "unfixable": "gray",
            },
        )
    )
    cols_o2[2].plotly_chart(
        ex.histogram(
            not_fixed_df[not_fixed_df["fix_category"] != "unfixable"].sort_values(
                by="date"
            ),
            x="ttpf",
            title="TTPF (overall)",
            color="fix_category",
            nbins=100,
            color_discrete_map={
                "dep_fixable": "red",
                "fixable": "orange",
            },
        )
    )

    cols_s2 = st.columns(3)
    cols_s2[0].plotly_chart(
        ex.histogram(
            fixed_df[fixed_df["fix_actor"] == "Workflow"].sort_values(by="date"),
            x="ttf",
            title="TTF (by workflow maint.)",
            nbins=100,
            color_discrete_sequence=["blue"],
        )
    )
    cols_s2[1].plotly_chart(
        ex.histogram(
            fixable_df.sort_values(by="date"),
            x="elapsed",
            title="OVA (fixable)",
            labels={"elapsed": "ova"},
            nbins=100,
            color_discrete_sequence=["orange"],
        )
    )
    cols_s2[2].plotly_chart(
        ex.histogram(
            fixable_df.sort_values(by="date"),
            x="ttpf",
            title="TTPF (fixable)",
            nbins=100,
            color_discrete_sequence=["orange"],
        )
    )

    cols_s_22 = st.columns(3)
    cols_s_22[0].plotly_chart(
        ex.histogram(
            fixed_df[fixed_df["fix_actor"] == "Action"].sort_values(by="date"),
            x="ttf",
            title="TTF (by action maint.)",
            nbins=100,
            color_discrete_sequence=["lightblue"],
        )
    )
    cols_s_22[1].plotly_chart(
        ex.histogram(
            fixable_deps_df.sort_values(by="date"),
            x="elapsed",
            title="OVA (fixable deps.)",
            labels={"elapsed": "ova"},
            nbins=100,
            color_discrete_sequence=["red"],
        )
    )
    cols_s_22[2].plotly_chart(
        ex.histogram(
            fixable_deps_df.sort_values(by="date"),
            x="ttpf",
            title="TTPF (fixable deps.)",
            nbins=100,
            color_discrete_sequence=["red"],
        )
    )

    cols_s_32 = st.columns(3)
    cols_s_32[0].empty()
    cols_s_32[1].plotly_chart(
        ex.histogram(
            non_fixable_df.sort_values(by="date"),
            x="elapsed",
            title="OVA (unfixable)",
            labels={"elapsed": "ova"},
            nbins=100,
            color_discrete_sequence=["gray"],
        )
    )
    cols_s_32[2].empty()

    # ===========================

    fig = ex.histogram(rug_pulls, x="action", title="# of Rug Pulls per Action")
    fig = fig.update_xaxes(categoryorder="total descending")

    fig1 = ex.histogram(
        x=[
            vuln.split("@v.")[0]
            for vulns in rug_pulls["vulns_list"].to_list()
            for vuln in vulns
        ],
        title="# of Used JS Vulnerable Dependencies",
    )
    fig1 = fig1.update_xaxes(categoryorder="total descending")

    fig2 = ex.histogram(
        x=[vuln for vulns in rug_pulls["vulns_list"].to_list() for vuln in vulns],
        title="# of Used JS Vulnerable Dependencies Versions",
    )
    fig2 = fig2.update_xaxes(categoryorder="total descending")

    _ = st.plotly_chart(fig)
    _ = st.plotly_chart(fig1)
    _ = st.plotly_chart(fig2)

    st.write("##### Table")

    all, fixed, not_fixed, fixable, dep_fixable, not_fixable = st.tabs(
        ["All", "Fixed", "Not Fixed", "Fixable", "Fixable Deps.", "Not Fixable"]
    )

    with all:
        _ = st.dataframe(rug_pulls)
    with fixed:
        _ = st.dataframe(fixed_df)
    with not_fixed:
        _ = st.dataframe(not_fixed_df)
    with fixable:
        _ = st.dataframe(fixable_df)
    with dep_fixable:
        _ = st.dataframe(fixable_deps_df)
    with not_fixable:
        _ = st.dataframe(non_fixable_df)


def make_gantt_charts():
    st.write("##### Gantt Charts")
    grouped_rug_pulls = compute_rug_pulls().groupby(["repo", "workflow"])

    begin = (st.session_state["curr_page_gantt"] - 1) * 10
    end = st.session_state["curr_page_gantt"] * 10

    make_paging_component(ceil(len(grouped_rug_pulls) / 10), "curr_page_gantt")

    group = 0

    for workflow, rug_pulls in grouped_rug_pulls:
        if group < begin:
            group += 1
            continue
        if group >= end:
            break

        st.write(f"###### {'/'.join(workflow)}")

        no_fix = rug_pulls[rug_pulls["fix_category"] != "fixed"]
        fixable = no_fix[rug_pulls["fix_category"] != "unfixable"]

        names = rug_pulls["action"]
        actions = (
            rug_pulls["action"]
            + "@"
            + rug_pulls["version"]
            + " ("
            + rug_pulls["date"].map(str)
            + ")"
        )
        start_dates = rug_pulls["date"].to_list()
        end_dates = where(
            rug_pulls["fix_category"] == "fixed",
            rug_pulls["fix_date"],
            rug_pulls["last"],
        )
        colors = where(
            rug_pulls["fix_category"] == "fixed", rug_pulls["fix_actor"], "Unfixed"
        )
        versions = rug_pulls["fix_version"].to_list()

        df = [
            dict(
                id=ind,
                Action=task,
                Start=start,
                Finish=finish,
                Fix_Actor=color,
                Fix_Version=", ".join(version),
            )
            for ind, task, start, finish, color, version in zip(
                names, actions, start_dates, end_dates, colors, versions
            )
        ]

        df.sort(key=lambda x: x["id"])

        st.write(rug_pulls)

        fig = ex.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Action",
            text="Fix_Version",
            color="Fix_Actor",
            color_discrete_map={
                "Workflow": "blue",
                "Action": "lightblue",
                "Unfixed": "lightgray",
            },
        )
        fig.add_scatter(
            x=fixable["fix_date"],
            y=fixable["action"]
            + "@"
            + fixable["version"]
            + " ("
            + fixable["date"].map(str)
            + ")",
            name="fix available",
            mode="markers",
            marker={"color": "green", "size": 10},
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(showgrid=True)

        st.plotly_chart(fig, key="/".join(workflow))

        group += 1

    make_paging_component(ceil(len(grouped_rug_pulls) / 10), "curr_page_gantt")
