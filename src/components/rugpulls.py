from math import ceil
from os.path import abspath, dirname, join

import plotly.express as ex
import streamlit as st
from numpy import where
from pandas import DataFrame, concat, read_csv
from plotly.io import write_image

from ..components.metrics import make_metrics_components
from ..components.paging import make_paging_component
from ..helpers.compute import compute_rug_pulls

GRAPH_COLORS = {
    "workflow": "#072955",
    "action": "#E02B33",
    "dependency": "#F0C572",
    "fixable": "#59A99B",
    "unfixable": "#CECECE",
    "commit": "#008DFF",
    "rugpull": "#D73034",
}


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

    workflow_maint = fixed[fixed["fix_actor"] == "Workflow"]
    action_maint = fixed[fixed["fix_actor"] == "Action"]

    make_metrics_components(
        labels=[
            "# Fixed",
            "% Fixed",
            "",
            "# By Workflow Maint.",
            "% By Workflow Maint.",
            "# By Action Maint.",
            "% By Action Maint.",
        ],
        values=[
            len(fixed),
            round(len(fixed) * 100 / len(rug_pulls), 2),
            "",
            len(workflow_maint),
            round(len(workflow_maint) * 100 / len(rug_pulls), 2),
            len(action_maint),
            round(len(action_maint) * 100 / len(rug_pulls), 2),
        ],
        colors=["green", "green", "", "green", "green", "green", "green"],
    )

    make_metrics_components(
        labels=[
            "# Not Fixed",
            "% Not Fixed",
            "",
            "# Fixable",
            "% Fixable",
            "# Fixable Deps.",
            "% Fixable Deps.",
        ],
        values=[
            len(not_fixed),
            round(len(not_fixed) * 100 / len(rug_pulls), 2),
            "",
            len(fixable),
            round(len(fixable) * 100 / len(rug_pulls), 2),
            len(fixable_deps),
            round(len(fixable_deps) * 100 / len(rug_pulls), 2),
        ],
        colors=["red", "red", "", "orange", "orange", "orange", "orange"],
    )

    make_metrics_components(
        labels=[
            "# Not Fixable",
            "% Not Fixable",
        ],
        values=[
            len(not_fixable),
            round(len(not_fixable) * 100 / len(rug_pulls), 2),
        ],
        colors=["gray", "gray"],
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

    fixed = rug_pulls[rug_pulls["fix_category"] == "fixed"]
    not_fixed = rug_pulls[rug_pulls["fix_category"] != "fixed"]
    fixable = not_fixed_df[not_fixed_df["fix_category"] != "unfixable"]
    not_fixable = not_fixed[not_fixed["fix_category"] == "unfixable"]

    make_metrics_components(
        labels=[
            "Min. TTX (days)",
            "Max. TTX (days)",
            "Med. TTX (days)",
            "MTTX (days)",
            "Std. TTX (days)",
        ],
        values=[
            int(fixed["ttx"].min() if len(fixed["ttx"]) > 0 else 0),
            int(fixed["ttx"].max() if len(fixed["ttx"]) > 0 else 0),
            int(fixed["ttx"].median() if len(fixed["ttx"]) > 0 else 0),
            round(fixed["ttx"].mean(), 2) if len(fixed["ttx"]) > 0 else 0,
            round(fixed["ttx"].std(), 2) if len(fixed["ttx"]) > 0 else 0,
        ],
    )

    make_metrics_components(
        labels=[
            "Min. TTPF (days)",
            "Max. TTPF (days)",
            "Med. TTPF (days)",
            "MTTPF (days)",
            "Std. TTPF (days)",
        ],
        values=[
            int(fixable["ttpf"].min()) if len(fixable["ttpf"]) > 0 else 0,
            int(fixable["ttpf"].max()) if len(fixable["ttpf"]) > 0 else 0,
            int(fixable["ttpf"].median()) if len(fixable["ttpf"]) > 0 else 0,
            round(fixable["ttpf"].mean(), 2) if len(fixable["ttpf"]) > 0 else 0,
            round(fixable["ttpf"].std(), 2) if len(fixable["ttpf"]) > 0 else 0,
        ],
    )

    make_metrics_components(
        labels=[
            "Min. OVA (days)",
            "Max. OVA (days)",
            "Med. OVA (days)",
            "MOVA (days)",
            "Std. OVA (days)",
        ],
        values=[
            int(not_fixed["elapsed"].dropna().min())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            int(not_fixed["elapsed"].dropna().max())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            int(not_fixed["elapsed"].dropna().median())
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            round(not_fixed["elapsed"].dropna().mean(), 2)
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
            round(not_fixed["elapsed"].dropna().std(), 2)
            if len(not_fixed["elapsed"].dropna()) > 0
            else 0,
        ],
    )

    cols_o2 = st.columns(3)

    figo21 = ex.histogram(
        fixed_df.sort_values(by="date"),
        x="ttx",
        color="fix_actor",
        title="TTX (overall)",
        nbins=100,
        color_discrete_map={
            "Workflow": GRAPH_COLORS["workflow"],
            "Action": GRAPH_COLORS["action"],
        },
        labels={
            "ttx": "TTX",
            "fix_actor": "Actor",
        },
        marginal="box",
        barmode="overlay",
    )
    figo21.data[0].name = "TTXw"
    figo21.data[2].name = "TTXa"
    figo21.update_layout(yaxis_title="rug pull count")

    figo21a = ex.scatter(
        fixed_df.sort_values(by="date"),
        x="date",
        y="ttx",
        color="fix_actor",
        color_discrete_map={
            "Workflow": GRAPH_COLORS["workflow"],
            "Action": GRAPH_COLORS["action"],
        },
        labels={
            "fix_actor": "Actor",
        },
    )

    figo21a.data[0].name = "TTXw"
    figo21a.data[1].name = "TTXa"
    figo21a.update_layout(yaxis_title="TTX")

    figo22 = ex.histogram(
        not_fixed_df.sort_values(by="date"),
        x="elapsed",
        title="OVA (overall)",
        labels={
            "elapsed": "OVA",
            "fix_category": "Type",
        },
        color="fix_category",
        nbins=100,
        color_discrete_map={
            "dep_fixable": GRAPH_COLORS["dependency"],
            "fixable": GRAPH_COLORS["fixable"],
            "unfixable": GRAPH_COLORS["unfixable"],
        },
        marginal="box",
        barmode="overlay",
    )
    figo22.data[0].name = "OVAj"
    figo22.data[2].name = "OVAa"
    figo22.data[4].name = "OVAu"
    figo22.update_layout(yaxis_title="rug pull count")

    figo22a = ex.scatter(
        not_fixed_df.sort_values(by="date"),
        x="date",
        y="elapsed",
        labels={
            "elapsed": "ova",
            "fix_category": "Type",
        },
        color="fix_category",
        color_discrete_map={
            "dep_fixable": GRAPH_COLORS["dependency"],
            "fixable": GRAPH_COLORS["fixable"],
            "unfixable": GRAPH_COLORS["unfixable"],
        },
    )

    figo22a.data[0].name = "OVAj"
    figo22a.data[1].name = "OVAa"
    figo22a.data[2].name = "OVAu"
    figo22a.update_layout(yaxis_title="OVA")

    figo23 = ex.histogram(
        not_fixed_df[not_fixed_df["fix_category"] != "unfixable"].sort_values(
            by="date"
        ),
        x="ttpf",
        title="TTPF (overall)",
        color="fix_category",
        nbins=100,
        color_discrete_map={
            "dep_fixable": GRAPH_COLORS["dependency"],
            "fixable": GRAPH_COLORS["fixable"],
        },
        labels={
            "ttpf": "TTPF",
            "fix_category": "Type",
        },
        marginal="box",
        barmode="overlay",
    )
    figo23.data[0].name = "TTPFj"
    figo23.data[2].name = "TTPFa"
    figo23.update_layout(yaxis_title="rug pull count")

    figo23a = ex.scatter(
        not_fixed_df[not_fixed_df["fix_category"] != "unfixable"].sort_values(
            by="date"
        ),
        x="date",
        y="ttpf",
        color="fix_category",
        color_discrete_map={
            "dep_fixable": GRAPH_COLORS["dependency"],
            "fixable": GRAPH_COLORS["fixable"],
        },
        labels={
            "fix_category": "Type",
        },
    )

    figo23a.data[0].name = "TTPFj"
    figo23a.data[1].name = "TTPFa"
    figo23a.update_layout(yaxis_title="TTPF")

    figo21.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo21a.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo22.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo22a.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo23.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    figo23a.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    cols_o2[0].plotly_chart(figo21)
    cols_o2[0].plotly_chart(figo21a)
    cols_o2[2].plotly_chart(figo22)
    cols_o2[2].plotly_chart(figo22a)
    cols_o2[1].plotly_chart(figo23)
    cols_o2[1].plotly_chart(figo23a)

    # ===========================

    deps_df = rug_pulls.explode("vulns_list")
    deps_df["vulns_list"] = deps_df["vulns_list"].apply(
        lambda x: x.split("@v.")[1].split(" - ")[1]
    )
    direct_indirect = deps_df[["date", "vulns_list"]].rename(
        columns={"vulns_list": "type"}
    )

    fig2 = ex.histogram(rug_pulls, x="action", title="# of Rug Pulls per Action")
    fig2 = fig2.update_xaxes(categoryorder="total descending")

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

    added_freqs = DataFrame(merged.groupby(by=["rug pulls", "uses"]).size())
    freqs1 = merged.merge(
        added_freqs, left_on=["rug pulls", "uses"], right_index=True, how="outer"
    ).rename(columns={0: "count"})
    
    st.write(actions_popularity.sum())

    fign = ex.scatter(
        freqs1,
        y="rug pulls",
        x="uses",
        color_discrete_sequence=[GRAPH_COLORS["workflow"]],
        labels={
            "rug pulls": "# rug pulled Actions",
            "uses": "# used Actions",
            "color": "density",
        },
        hover_data={"name": freqs1["action"]},
        log_x=True,
        log_y=True,
    )

    st.dataframe(freqs1)

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
        color_continuous_scale=[GRAPH_COLORS["workflow"], GRAPH_COLORS["action"]],
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
            "commit": GRAPH_COLORS["commit"],
            "rug pull": GRAPH_COLORS["rugpull"],
        },
    )

    fig3.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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

    st.plotly_chart(fig)
    st.plotly_chart(fig1)

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

    # _ = st.plotly_chart(fig2)

    direct_indirect_df = (
        rug_pulls.explode("vulns_list")[
            [
                "action",
                "vulns_list",
                "vulns_severities",
                "date",
                "fix_category",
                "fix_actor",
                "version",
            ]
        ]
        .explode("vulns_severities")
        .sort_values(by="date")
    )
    direct_indirect_df["version"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[0].split("@v.")[1]
    )
    direct_indirect_df["vuln"] = direct_indirect_df["vulns_severities"].apply(
        lambda x: x.split(" // ")[0]
    )
    direct_indirect_df["vuln1"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[0].split("@v.")[0]
    )

    direct_indirect_df["used as"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[1]
    )
    direct_indirect_df["vulns_list"] = direct_indirect_df["vulns_list"].apply(
        lambda x: x.split(" - ")[0]
    )
    direct_indirect_df["cve"] = direct_indirect_df["vulns_severities"].apply(
        lambda x: x.split(" // ")[1]
    )
    direct_indirect_df["severity"] = (
        direct_indirect_df["vulns_severities"]
        .apply(lambda x: x.split(" // ")[2])
        .map(float)
    )

    direct_indirect_df = direct_indirect_df[
        direct_indirect_df[["vuln", "vuln1"]].nunique(axis=1) == 1
    ]

    make_metrics_components(
        labels=[
            "Most Occurring CVE",
            "Occurrences",
            "Distinct CVEs",
        ],
        values=[
            direct_indirect_df["cve"]
            .value_counts()
            .sort_values(ascending=False)
            .index[0],
            direct_indirect_df["cve"]
            .value_counts()
            .sort_values(ascending=False)
            .iloc[0],
            direct_indirect_df["cve"].nunique(),
        ],
    )

    make_metrics_components(
        labels=[
            "Min. CVSS Score",
            "Max. CVSS Score",
            "Med. CVSS Score",
            "Mean CVSS Score",
            "Std. CVSS Score",
        ],
        values=[
            direct_indirect_df[direct_indirect_df["severity"] > 0.0]["severity"].min(),
            direct_indirect_df[direct_indirect_df["severity"] > 0.0]["severity"].max(),
            direct_indirect_df[direct_indirect_df["severity"] > 0.0][
                "severity"
            ].median(),
            round(
                direct_indirect_df[direct_indirect_df["severity"] > 0.0][
                    "severity"
                ].mean(),
                2,
            ),
            round(
                direct_indirect_df[direct_indirect_df["severity"] > 0.0][
                    "severity"
                ].std(),
                2,
            ),
        ],
    )

    direct_indirect_df["fix_actor"] = direct_indirect_df["fix_actor"].fillna("")
    direct_indirect_df["fix_category"] = (
        direct_indirect_df["fix_category"] + " " + direct_indirect_df["fix_actor"]
    )

    histo = ex.histogram(
        direct_indirect_df[direct_indirect_df["severity"] > 0.0],
        x="severity",
        color="fix_category",
        color_discrete_sequence=[
            GRAPH_COLORS["workflow"],
            GRAPH_COLORS["action"],
            GRAPH_COLORS["dependency"],
            GRAPH_COLORS["fixable"],
            GRAPH_COLORS["unfixable"],
        ],
        nbins=16,
        labels={
            "severity": "CVSS",
            "fix_category": "Category",
        },
    )

    histo.data[0].name = "Fixed (Workflow)"
    histo.data[1].name = "Fixed (Action)"
    histo.data[2].name = "Fixable (JS Dep.)"
    histo.data[3].name = "Fixable (Action)"
    histo.data[4].name = "Unfixable"
    histo.update_layout(yaxis_title="# used dependencies")
    histo.update_xaxes(range=[0, 10.0])

    histo.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(histo)
    
    # histo.update_layout(
    #     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    # )

    # histo.update_layout(yaxis_title="% rug pull")
    histo.update_xaxes(showgrid=False, zeroline=False)
    histo.update_yaxes(showgrid=True, zeroline=False)

    write_image(histo, "./cvss-histo.pdf", format="pdf")

    sev_horizontal = st.container(horizontal=True)

    gt0 = direct_indirect_df[direct_indirect_df["severity"] > 0.0]
    gt0["rp"] = gt0["action"] + gt0["version"] + gt0["date"].apply(str)
    gt0 = gt0.groupby(by="severity")["rp"].apply(set).apply(lambda x: len(x)).reset_index()

    sev_horizontal.text(
        f"Low: {gt0[(gt0['severity'] >= 0.1) & (gt0['severity'] <= 3.99)]["rp"].sum()}"
    )
    sev_horizontal.text(
        f"Medium: {gt0[(gt0['severity'] >= 3.0) & (gt0['severity'] <= 6.99)]["rp"].sum()}"
    )
    sev_horizontal.text(
        f"High: {gt0[(gt0['severity'] >= 7.0) & (gt0['severity'] <= 8.99)]["rp"].sum()}"
    )
    sev_horizontal.text(
        f"Critical: {gt0[(gt0['severity'] >= 9.0) & (gt0['severity'] <= 10.0)]["rp"].sum()}"
    )

    figo21.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    cves_cols = st.columns(2)

    cves = (
        direct_indirect_df[["cve", "vuln"]]
        .groupby(by="vuln")["cve"]
        .apply(set)
        .reset_index()
        .set_index("vuln")
    )
    sevs = (
        direct_indirect_df[["vuln", "severity"]]
        .groupby(by="vuln")["severity"]
        .apply(set)
        .reset_index()
        .set_index("vuln")
    )
    cves["length"] = cves["cve"].str.len()
    sevs["length"] = sevs["severity"].str.len()

    cves_cols[0].dataframe(cves.sort_values(by="length", ascending=False))
    cves_cols[1].dataframe(sevs.sort_values(by="length", ascending=False))

    direct_df = (
        direct_indirect_df[direct_indirect_df["used as"] == "direct"][
            ["cve", "severity", "vuln"]
        ]
        .value_counts()
        .sort_values(ascending=False)
    )
    indirect_df = (
        direct_indirect_df[direct_indirect_df["used as"] == "indirect"][
            ["cve", "severity", "vuln"]
        ]
        .value_counts()
        .sort_values(ascending=False)
    )
    total_df = (
        direct_indirect_df[["cve", "severity", "vulns_list"]]
        .value_counts()
        .sort_values(ascending=False)
    )

    cols_deps = st.columns(3)
    cols_deps[0].write("##### Direct Dependencies")
    cols_deps[0].dataframe(direct_df)
    cols_deps[1].write("##### Indirect Dependencies")
    cols_deps[1].dataframe(indirect_df)
    cols_deps[2].write("##### Dependencies")
    cols_deps[2].dataframe(total_df)

    st.dataframe(
        DataFrame(direct_df)
        .merge(
            DataFrame(indirect_df),
            left_index=True,
            right_index=True,
            how="outer",
        )
        .reset_index()
        .set_index(["cve", "severity", "vuln"])
        .merge(
            DataFrame(total_df),
            left_index=True,
            right_index=True,
            how="outer",
        )
        .dropna()
        .rename(columns={"count_x": "direct", "count_y": "indirect", "count": "total"})
        .sort_values(by="total", ascending=False)
    )


def make_gantt_charts():
    rug_pulls = compute_rug_pulls()
    fixed_df = rug_pulls[rug_pulls["fix_category"] == "fixed"]
    not_fixed_df = rug_pulls[rug_pulls["fix_category"] != "fixed"]
    fixable_df = not_fixed_df[not_fixed_df["fix_category"] == "fixable"]
    fixable_deps_df = not_fixed_df[not_fixed_df["fix_category"] == "dep_fixable"]
    non_fixable_df = rug_pulls[rug_pulls["fix_category"] == "unfixable"]

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
            labels={"Fix_Actor": "Actor"},
            color_discrete_map={
                "Workflow": GRAPH_COLORS["workflow"],
                "Action": GRAPH_COLORS["action"],
                "Unfixed": GRAPH_COLORS["unfixable"],
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
            marker={"color": "#4FCB8C", "size": 10},
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(showgrid=True)

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, key="/".join(workflow))

        group += 1

    make_paging_component(ceil(len(grouped_rug_pulls) / 10), "curr_page_gantt")
