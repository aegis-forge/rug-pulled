from math import ceil

import streamlit as st

from src.components.metrics import make_metrics_components

from ..components.paging import make_paging_component
from ..helpers.compute import compute_rug_pulls


def make_rug_pulls_component() -> None:
    begin = (st.session_state["curr_page_rug_pulls"] - 1) * 10
    end = st.session_state["curr_page_rug_pulls"] * 10

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

    rug_pulls = compute_rug_pulls()
    cut_rug_pulls = {col: rug_pull[begin:end] for col, rug_pull in rug_pulls.items()}

    fixed = rug_pulls[rug_pulls["Fixed By"] != "—"]
    not_fixed = rug_pulls[rug_pulls["Fixed By"] == "—"]

    make_metrics_components(
        labels=[
            "# Fixed",
            "% Fixed",
            "Workflow Maint.",
            "Action Maint.",
            "Min. TTF (days)",
            "Avg. TTF (days)",
            "Max. TTF (days)",
        ],
        values=[
            len(fixed),
            round(len(fixed) * 100 / len(rug_pulls), 1),
            len(fixed[fixed["Fixed By"].str.contains("Workflow")]),
            len(fixed[fixed["Fixed By"].str.contains("Action")]),
            fixed.loc[:, "TTF (days)"].min(),
            round(fixed.loc[:, "TTF (days)"].mean()),
            fixed.loc[:, "TTF (days)"].max(),
        ],
        colors=["green", "green", "", "", "", "", ""],
    )

    make_metrics_components(
        labels=["# Not Fixed", "% Not Fixed"],
        values=[len(not_fixed), round(len(not_fixed) * 100 / len(rug_pulls), 1)],
        colors=["red", "red"],
    )

    _ = st.table(cut_rug_pulls, border="horizontal")

    make_paging_component(
        ceil(len(rug_pulls["Action"]) / 10),
        "curr_page_rug_pulls",
    )
