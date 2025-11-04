import streamlit as st

from math import ceil

from ..components.paging import make_paging_component
from ..helpers.compute import compute_rug_pulls


def make_rug_pulls_component() -> None:    
    begin = (st.session_state["curr_page_rug_pulls"] - 1) * 10
    end = st.session_state["curr_page_rug_pulls"] * 10
    
    rug_pulls = compute_rug_pulls(st.session_state["curr_page_rug_pulls"])
    # cut_rug_pulls = {
    #     col: rug_pull[begin:end]
    #     for col, rug_pull in rug_pulls.items()
    # }

    # rug_pulled_workflows_title = st.container(
    #     horizontal=True,
    #     vertical_alignment="center",
    # )
    # rug_pulled_workflows_title.write("#### Rug-Pulled Workflow Commits")
    # _ = rug_pulled_workflows_title.text(
    #     body="",
    #     help="Rug-pulled workflow commits are those commits where the maintainers of"
    #     + " the used Actions upgrade/downgrade their versions. By doing so, they introduce"
    #     + " vulnerabilities in the workflow. Workflow maintainers do not introduce these"
    #     + " vulnerabilities directly.",
    # )
    
    # _ = st.table(cut_rug_pulls, border="horizontal")
    
    # make_paging_component(
    #     ceil(len(rug_pulls["Commit"]) / 10),
    #     "curr_page_rug_pulls",
    # )
