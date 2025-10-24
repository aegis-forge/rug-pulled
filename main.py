import streamlit as st

from dotenv import dotenv_values
from os.path import join, dirname, abspath

from src.helpers.pickling import pickle2repo
from src.helpers.repos import get_repo_names
from src.models.db import Repository
from src.plots.correlations import correlation_plot
from src.plots.timelines import timelines_plot, timelines_statistics
from src.plots.init import compute_vals


# Initialization
params = dotenv_values(join(dirname(abspath(__file__)), ".env"))

repo_names = get_repo_names(params)
current_repos: list[Repository] = []

st.set_page_config(layout="wide")

if "max_repo_selections" not in st.session_state:
    st.session_state["max_repo_selections"] = len(repo_names)

if "selected_repos" not in st.session_state:
    st.session_state["selected_repos"] = {}

if "current_workflows" not in st.session_state:
    st.session_state["current_workflows"] = []

if "selected_workflows" not in st.session_state:
    st.session_state["selected_workflows"] = {}
    
if "results_repos" not in st.session_state:
    st.session_state["results_repos"] = {}


# Callbacks
def options_select():
    if (
        "selected_repos_options" not in st.session_state
        or "selected_workflows_options" not in st.session_state
    ):
        return

    if "All" in st.session_state["selected_repos_options"]:
        st.session_state["selected_repos_options"] = ["All"]
        st.session_state["max_repo_selections"] = 1
    else:
        st.session_state["max_repo_selections"] = len(repo_names)

    selected_options = st.session_state["selected_repos_options"]
    repos = selected_options if "All" not in selected_options else repo_names

    st.session_state["selected_repos"] = {}
    st.session_state["current_workflows"] = []
    st.session_state["selected_workflows"] = {}

    for repo in repos:
        repo_obj = pickle2repo(f"{repo.replace('/', '::')}")
        st.session_state["selected_repos"][repo] = repo_obj

        if len(repos) > 1:
            st.session_state["selected_workflows"][repo] = repo_obj.workflows

        st.session_state["current_workflows"].extend(list(repo_obj.workflows.keys()))


def get_workflows():
    repo_name = list(st.session_state["selected_repos"].keys())[0]
    workflow_names = st.session_state["selected_repos"][repo_name].workflows.keys()

    st.session_state["selected_workflows"] = {repo_name: {}}

    for workflow in st.session_state["selected_workflows_options"]:
        if workflow in workflow_names:
            st.session_state["selected_workflows"][repo_name][workflow] = (
                st.session_state["selected_repos"][repo_name].workflows[workflow]
            )


# Page Components
body_container = st.container(gap="large")
header_container = body_container.container(horizontal=True, horizontal_alignment="center")
filter_container = body_container.container()
workflows_container = filter_container.container(horizontal=True, vertical_alignment="bottom")


_ = header_container.image(
    image=join(dirname(abspath(__file__)), "./static/vectors/logo.svg"),
    width=100,
)
_ = header_container.title("Kleio")


_ = workflows_container.multiselect(
    label="Repositories",
    options=["All", *repo_names],
    max_selections=st.session_state["max_repo_selections"],
    placeholder="Select repositories",
    help="Select one or more repositories (N.B. when selecting 'All', expect some loading time)",
    on_change=options_select,
    key="selected_repos_options",
)
_ = workflows_container.multiselect(
    label="Workflows",
    options=st.session_state["current_workflows"],
    placeholder="Select workflows",
    disabled=len(st.session_state["selected_repos"]) != 1,
    help="Single workflows can only be selected only with one repository. If multiple repositories are selected, all of their workflows will be selected.",
    on_change=get_workflows,
    key="selected_workflows_options",
)


timelines, corrs, = st.tabs(["Timelines", "Correlations"])

if len(st.session_state["selected_workflows"]) == 0: 
    st.session_state["results_repos"] = {}

if len(st.session_state["selected_workflows"]) > 0:
    for repo, workflows in st.session_state["selected_workflows"].items():
        st.session_state["results_repos"][repo] = compute_vals(workflows)
        
    with timelines:
        statistics_plots = st.container()
        statistics_plots.write("#### Statistics")
        
        timelines_statistics()
        
        plot_header_container = st.container(horizontal=True, vertical_alignment="center")
        plot_header_container.write("#### Plots")
        show_timelines = plot_header_container.toggle(label="Show plots")
    
        if show_timelines:
            for repo, workflows in st.session_state["results_repos"].items():
                timelines_plot(repo, workflows)
    
    with corrs:
        st.write("#### Filters")
        
        axis_select_container = st.container(horizontal=True)
        
        _ = axis_select_container.selectbox(
            label="Y Axis",
            options=["% of dependency changes", "# of dependency changes"],
            key="correlations_y_filter",
        )
        
        st.write("#### Plots")
    
        for repo, workflows in st.session_state["results_repos"].items():
            correlation_plot(repo, workflows)
else:
    st.write("Please select at least one workflow")
