from json import load
from os.path import abspath, dirname, join

import streamlit as st

from ..helpers.repos import get_repo_names


def init_session_variables() -> None:
    st.set_page_config(
        page_title="kleio",
        page_icon="./static/vectors/favicon.svg",
        layout="wide",
    )

    if "repo_names" not in st.session_state:
        st.session_state["repo_names"] = sorted(get_repo_names())

    if "max_repo_selections" not in st.session_state:
        st.session_state["max_repo_selections"] = len(st.session_state["repo_names"])

    if "selected_repos" not in st.session_state:
        st.session_state["selected_repos"] = {}

    if "current_workflows" not in st.session_state:
        st.session_state["current_workflows"] = []

    if "selected_workflows" not in st.session_state:
        st.session_state["selected_workflows"] = {}

    if "results_repos" not in st.session_state:
        st.session_state["results_repos"] = {}

    if "rug_pulls_filter" not in st.session_state:
        st.session_state["rug_pulls_filter"] = "all"

    if "curr_page_timelines" not in st.session_state:
        st.session_state["curr_page_timelines"] = 1

    if "curr_page_gantt" not in st.session_state:
        st.session_state["curr_page_gantt"] = 1

    workflows = join(dirname(abspath(__file__)), "../../data/workflows.json")
    commits = join(dirname(abspath(__file__)), "../../data/commits.json")

    with open(workflows) as file:
        st.session_state["selected_workflows"] = load(file)

    with open(commits) as file:
        st.session_state["selected_commits"] = load(file)
