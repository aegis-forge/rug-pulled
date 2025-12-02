from math import ceil
from os.path import abspath, dirname, join

import plotly
import plotly.express as ex
import streamlit as st
from numpy import where
from pandas import DataFrame, concat, read_csv
from plotly.io import write_image
from scipy import stats

from ..components.metrics import make_metrics_components
from ..components.paging import make_paging_component
from ..helpers.compute import compute_rug_pulls


def _make_rug_pulls_metrics(rug_pulls: DataFrame) -> None:
    fixed = rug_pulls[rug_pulls["fix_category"] == "fixed"]
    not_fixed = rug_pulls[rug_pulls["fix_category"] != "fixed"]
    fixable = not_fixed[not_fixed["fix_category"] == "fixable"]
    fixable_deps = not_fixed[not_fixed["fix_category"] == "dep_fixable"]
    not_fixable = not_fixed[not_fixed["fix_category"] == "unfixable"]

    per_repo = rug_pulls.groupby(by=["repo"]).size()
    per_workflow = rug_pulls.groupby(by=["repo", "workflow"]).size()
    per_commit = rug_pulls.groupby(by=["repo", "workflow", "hash"]).size()
    per_action = rug_pulls.groupby(by=["action"]).size()
    per_action_version = rug_pulls.groupby(by=["action", "version"]).size()

    make_metrics_components(
        labels=[
            "# Rug Pulls",
            "# RP Repositories",
            "# RP Workflows",
            "# RP Commits",
            "# RP Actions",
            "# RP Action Versions",
        ],
        values=[
            int(len(rug_pulls)),
            len(rug_pulls.groupby(["repo"])),
            len(rug_pulls.groupby(["repo", "workflow"])),
            len(rug_pulls.groupby(["repo", "workflow", "hash"])),
            len(rug_pulls.groupby(["action"])),
            len(rug_pulls.groupby(["action", "version"])),
        ],
    )

    st.dataframe(
        DataFrame(
            {
                "element": [
                    "repository",
                    "workflow",
                    "commit",
                    "action",
                    "action version",
                ],
                "min": [
                    int(per_repo.min()),
                    int(per_workflow.min()),
                    int(per_commit.min()),
                    int(per_action.min()),
                    int(per_action_version.min()),
                ],
                "max": [
                    int(per_repo.max()),
                    int(per_workflow.max()),
                    int(per_commit.max()),
                    int(per_action.max()),
                    int(per_action_version.max()),
                ],
                "mean": [
                    round(float(per_repo.mean()), 2),
                    round(float(per_workflow.mean()), 2),
                    round(float(per_commit.mean()), 2),
                    round(float(per_action.mean()), 2),
                    round(float(per_action_version.mean()), 2),
                ],
                "median": [
                    int(per_repo.median()),
                    int(per_workflow.median()),
                    int(per_commit.median()),
                    int(per_action.median()),
                    int(per_action_version.median()),
                ],
                "stdev": [
                    round(float(per_repo.std()), 2),
                    round(float(per_workflow.std()), 2),
                    round(float(per_commit.std()), 2),
                    round(float(per_action.std()), 2),
                    round(float(per_action_version.std()), 2),
                ],
            }
        ),
        hide_index=True,
    )

    make_metrics_components(
        labels=[
            "# Fixed",
            "% Fixed",
            "MTTX (days)",
            "Min. TTX (days)",
            "Max. TTX (days)",
            "Med. TTX (days)",
        ],
        values=[
            len(fixed),
            round(len(fixed) * 100 / len(rug_pulls), 2),
            round(fixed["ttx"].mean(), 2) if len(fixed["ttx"]) > 0 else 0,
            int(fixed["ttx"].min()) if len(fixed["ttx"]) > 0 else 0,
            int(fixed["ttx"].max()) if len(fixed["ttx"]) > 0 else 0,
            int(fixed["ttx"].median()) if len(fixed["ttx"]) > 0 else 0,
        ],
        colors=["green", "green", "", "", "", ""],
    )

    workflow_maint = fixed[fixed["fix_actor"] == "Workflow"]
    action_maint = fixed[fixed["fix_actor"] == "Action"]

    make_metrics_components(
        labels=[
            "# By Workflow Maint.",
            "% By Workflow Maint.",
            "MTTX (days)",
            "Min. TTX (days)",
            "Max. TTX (days)",
            "Med. TTX (days)",
        ],
        values=[
            len(workflow_maint),
            round(len(workflow_maint) * 100 / len(rug_pulls), 2),
            round(workflow_maint["ttx"].mean(), 2)
            if len(workflow_maint["ttx"]) > 0
            else 0,
            workflow_maint["ttx"].min() if len(workflow_maint["ttx"]) > 0 else 0,
            workflow_maint["ttx"].max() if len(workflow_maint["ttx"]) > 0 else 0,
            workflow_maint["ttx"].median(),
        ],
        colors=["green", "green", "", "", "", ""],
    )

    make_metrics_components(
        labels=[
            "# By Action Maint.",
            "% By Action Maint.",
            "MTTX (days)",
            "Min. TTX (days)",
            "Max. TTX (days)",
            "Med. TTX (days)",
        ],
        values=[
            len(action_maint),
            round(len(action_maint) * 100 / len(rug_pulls), 2),
            round(action_maint["ttx"].mean(), 2) if len(action_maint["ttx"]) > 0 else 0,
            action_maint["ttx"].min() if len(action_maint["ttx"]) > 0 else 0,
            action_maint["ttx"].max() if len(action_maint["ttx"]) > 0 else 0,
            action_maint["ttx"].median() if len(action_maint["ttx"]) > 0 else 0,
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
    dataset = read_csv(join(dirname(abspath(__file__)), "../../data/dataset_stats.csv"))

    make_metrics_components(
        labels=[
            "# Repositories",
            "# Workflows",
            "# Commits",
            "# Actions",
            "# Action Versions",
            "# Dependencies",
            "# Dependency Versions",
            "# Vulnerabilities",
        ],
        values=[
            int(dataset[dataset["element"] == "repository"]["total"]),
            int(dataset[dataset["element"] == "workflow"]["total"]),
            int(dataset[dataset["element"] == "commit (per workflow)"]["total"]),
            int(dataset[dataset["element"] == "action (per commit)"]["unique"]),
            int(dataset[dataset["element"] == "action version (per commit)"]["unique"]),
            int(dataset[dataset["element"] == "dependency (per action)"]["unique"]),
            int(
                dataset[dataset["element"] == "dependency version (per action)"][
                    "unique"
                ]
            ),
            int(dataset[dataset["element"] == "vulnerability (per commit)"]["unique"]),
        ],
    )

    st.dataframe(dataset.drop("unique", axis=1), hide_index=True)
    _make_rug_pulls_metrics(rug_pulls)

    # ===========================

    st.write("##### Plots")

    cols_o = st.columns(3)

    figo1 = ex.scatter(
        fixed_df.sort_values(by="date"),
        x="date",
        y="ttx",
        color="fix_actor",
        title="TTX (overall)",
        color_discrete_map={"Workflow": "blue", "Action": "lightblue"},
    )
    figo2 = ex.scatter(
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
    figo3 = ex.scatter(
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

    figo1.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo2.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo3.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    cols_o[0].plotly_chart(figo1)
    cols_o[1].plotly_chart(figo2)
    cols_o[2].plotly_chart(figo3)

    cols_s = st.columns(3)
    cols_s[0].plotly_chart(
        ex.scatter(
            fixed_df[fixed_df["fix_actor"] == "Workflow"].sort_values(by="date"),
            x="date",
            y="ttx",
            title="TTX (by workflow maint.)",
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
            y="ttx",
            title="TTX (by action maint.)",
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

    cols_o2 = st.columns(3)

    figo21 = ex.histogram(
        fixed_df.sort_values(by="date"),
        x="ttx",
        color="fix_actor",
        title="TTX (overall)",
        nbins=100,
        color_discrete_map={"Workflow": "blue", "Action": "lightblue"},
        marginal="box",
        barmode="overlay",
    )
    figo22 = ex.histogram(
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
        marginal="box",
        barmode="overlay",
    )
    figo23 = ex.histogram(
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
        marginal="box",
        barmode="overlay",
    )

    figo21.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo22.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo23.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    cols_o2[0].plotly_chart(figo21)
    cols_o2[1].plotly_chart(figo22)
    cols_o2[2].plotly_chart(figo23)

    cols_s2 = st.columns(3)
    cols_s2[0].plotly_chart(
        ex.histogram(
            fixed_df[fixed_df["fix_actor"] == "Workflow"].sort_values(by="date"),
            x="ttx",
            title="TTX (by workflow maint.)",
            nbins=100,
            color_discrete_sequence=["blue"],
            marginal="box",
            barmode="overlay",
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
            marginal="box",
            barmode="overlay",
        )
    )
    cols_s2[2].plotly_chart(
        ex.histogram(
            fixable_df.sort_values(by="date"),
            x="ttpf",
            title="TTPF (fixable)",
            nbins=100,
            color_discrete_sequence=["orange"],
            marginal="box",
            barmode="overlay",
        )
    )

    cols_s_22 = st.columns(3)
    cols_s_22[0].plotly_chart(
        ex.histogram(
            fixed_df[fixed_df["fix_actor"] == "Action"].sort_values(by="date"),
            x="ttx",
            title="TTX (by action maint.)",
            nbins=100,
            color_discrete_sequence=["lightblue"],
            marginal="box",
            barmode="overlay",
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
            marginal="box",
            barmode="overlay",
        )
    )
    cols_s_22[2].plotly_chart(
        ex.histogram(
            fixable_deps_df.sort_values(by="date"),
            x="ttpf",
            title="TTPF (fixable deps.)",
            nbins=100,
            color_discrete_sequence=["red"],
            marginal="box",
            barmode="overlay",
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
            marginal="box",
            barmode="overlay",
        )
    )
    cols_s_32[2].empty()
    
    # st.plotly_chart(ex.box(fixed_df, y="ttx", color="fix_actor").add_box(fixable_df, y="ttpf"))

    # ===========================

    deps_df = rug_pulls.explode("vulns_list")
    deps_df["vulns_list"] = deps_df["vulns_list"].apply(
        lambda x: x.split("@v.")[1].split(" - ")[1]
    )
    direct_indirect = deps_df[["date", "vulns_list"]].rename(
        columns={"vulns_list": "type"}
    )

    fig = ex.histogram(
        direct_indirect.sort_values(by="date"),
        x="date",
        color="type",
        color_discrete_map={
            "direct": "blue",
            "indirect": "lightblue",
            "direct_dev": "red",
        },
    )

    fig1 = ex.histogram(
        direct_indirect.sort_values(by="date"),
        x="date",
        color="type",
        barnorm="fraction",
        color_discrete_map={
            "direct": "blue",
            "indirect": "lightblue",
            "direct_dev": "red",
        },
    )

    fig2 = ex.histogram(rug_pulls, x="action", title="# of Rug Pulls per Action")
    fig2 = fig2.update_xaxes(categoryorder="total descending")

    fig4 = ex.histogram(
        x=[vuln for vulns in rug_pulls["vulns_list"].to_list() for vuln in vulns],
        title="# of Used JS Vulnerable Dependencies Versions",
    )
    fig4 = fig4.update_xaxes(categoryorder="total descending")

    commit_dates = read_csv(
        join(dirname(abspath(__file__)), "../../data/commit_dates.csv")
    )
    commit_dates["date"] = commit_dates["date"].astype("datetime64[s]")
    commit_dates["type"] = ["commit" for _ in range(len(commit_dates))]
    rug_pull_dates = DataFrame(
        {
            "date": rug_pulls["date"],
            "type": ["rug pull" for _ in range(len(rug_pulls["date"]))],
        }
    )

    df = concat([commit_dates, rug_pull_dates])

    actions_popularity = read_csv(
        join(dirname(abspath(__file__)), "../../data/actions.csv")
    )

    actions_popularity = actions_popularity.sort_values(by="action").set_index("action")
    action_versions = read_csv(
        join(dirname(abspath(__file__)), "../../data/actions_versions.csv")
    ).set_index("action")
    rp_action_versions = (
        rug_pulls[["action", "date"]].drop_duplicates().groupby(by="action").count()
    )
    actions_rugpulls = (
        DataFrame([rug_pulls["action"].value_counts().rename("rps")])
        .melt()
        .set_index("action")
        .sort_values(by="action")
    )
    merged = (
        actions_rugpulls.merge(
            actions_popularity, left_index=True, right_index=True, how="outer"
        )
        .merge(rp_action_versions, left_index=True, right_index=True, how="outer")
        .merge(action_versions, left_index=True, right_index=True, how="outer")
        .reset_index()
        .rename(
            columns={
                "count": "uses",
                "value": "rug pulls",
                "action_d": "versions",
                "date": "rp versions",
            }
        )
    ).fillna(0)

    fign = ex.scatter(
        merged,
        y="uses",
        x="rug pulls",
        labels={"rug pulls": "# rug pulls", "uses": "# uses"},
        hover_data={"name": merged["action"]},
    )

    max_xy = max(merged["versions"].max(), merged["rp versions"].max()) + 1

    added_freqs = DataFrame(merged.groupby(by=["rp versions", "versions"]).size())
    freqs = merged.merge(
        added_freqs, left_on=["rp versions", "versions"], right_index=True, how="outer"
    ).rename(columns={0: "count"})

    fign1 = ex.scatter(
        freqs,
        y="rp versions",
        x="versions",
        color="count",
        color_continuous_scale=["#7C7CFC", "#FC7C7C"],
        labels={
            "rp versions": "# rug pulled versions",
            "versions": "# used versions",
            "color": "density",
        },
        hover_data={"name": freqs["action"]},
        range_x=[0, max_xy],
        range_y=[-1, max_xy],
    ).add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=max_xy,
        y1=max_xy,
        line={"dash": "dash", "color": "gray"},
        opacity=0.3,
    )

    fig3 = ex.histogram(
        df,
        x="date",
        histfunc="count",
        color="type",
        marginal="box",
        barmode="overlay",
        color_discrete_map={
            "commit": "blue",
            "rug pull": "red",
        },
    )

    fig3.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    _ = st.plotly_chart(fig3, key="hist")

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig1.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.dataframe(merged.sort_values(by="rug pulls", ascending=False))

    coln = st.columns(2)
    coln[0].plotly_chart(fign)
    coln[1].plotly_chart(fign1)

    col = st.columns(2)
    col[0].plotly_chart(fig)
    col[1].plotly_chart(fig1)

    # _ = st.plotly_chart(fig2)

    direct_indirect_df = rug_pulls.explode("vulns_list")[
        ["action", "vulns_list", "vulns_severities"]
    ]
    direct_indirect_df["used as"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[1]
    )
    direct_indirect_df["vulns_list"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[0].split("@v.")[0]
    )

    st.dataframe(direct_indirect_df)

    cols_deps = st.columns(3)
    cols_deps[2].dataframe(
        direct_indirect_df[["vulns_list"]].value_counts().sort_values(ascending=False)
    )
    cols_deps[0].dataframe(
        direct_indirect_df[direct_indirect_df["used as"] == "direct"][
            ["vulns_list", "used as"]
        ]
        .value_counts()
        .sort_values(ascending=False)
    )
    cols_deps[1].dataframe(
        direct_indirect_df[direct_indirect_df["used as"] == "indirect"][
            ["vulns_list", "used as"]
        ]
        .value_counts()
        .sort_values(ascending=False)
    )

    _ = st.plotly_chart(fig4)

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
        
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, key="/".join(workflow))
        
        # if '/'.join(workflow) == "adobe-consulting-services/acs-aem-commons/maven.yml":
        #     fig.update_xaxes(showgrid=False, zeroline=False)
        #     fig.update_yaxes(showgrid=True, zeroline=False)
        
        #     write_image(fig, "./gantt.pdf", format="pdf", width=1000)

        group += 1

    make_paging_component(ceil(len(grouped_rug_pulls) / 10), "curr_page_gantt")
