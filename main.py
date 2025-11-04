import streamlit as st

from os.path import join, dirname, abspath

from src.components.correlations import make_rug_pulls_component
from src.components.timelines import make_timelines_component, make_statistics_component
from src.init.variables import init_session_variables
from src.init.callbacks import options_select, get_workflows
from src.plots.init import compute_vals


# Initialization
ss = st.session_state
init_session_variables()


# Page Components
body_container = st.container(gap="large")
header_container = body_container.container(
    horizontal=True, horizontal_alignment="center"
)
filter_container = body_container.container()
workflows_container = filter_container.container(
    horizontal=True, vertical_alignment="bottom"
)


_ = header_container.image(
    image=join(dirname(abspath(__file__)), "./static/vectors/logo.svg"),
    width=100,
)
_ = header_container.title("Kleio")


_ = workflows_container.multiselect(
    label="Repositories",
    options=["All", *ss["repo_names"]],
    max_selections=ss["max_repo_selections"],
    placeholder="Select repositories",
    help="Select one or more repositories (N.B. when selecting 'All', expect some loading time)",
    on_change=options_select,
    key="selected_repos_options",
)
_ = workflows_container.multiselect(
    label="Workflows",
    options=ss["current_workflows"],
    placeholder="Select workflows",
    disabled=len(ss["selected_repos"]) != 1,
    help="Single workflows can only be selected only with one repository. If multiple repositories are selected, all of their workflows will be selected automatically.",
    on_change=get_workflows,
    key="selected_workflows_options",
)


timelines, corrs = st.tabs(["Timelines", "Correlations"])

if len(ss["selected_workflows"]) == 0:
    ss["results_repos"] = {}

if len(ss["selected_workflows"]) > 0:
    for repo, workflows in ss["selected_workflows"].items():
        ss["results_repos"][repo] = compute_vals(workflows)

    with timelines:
        make_statistics_component()
        make_timelines_component()
    with corrs:
        make_rug_pulls_component()

        # st.write("#### Correlation Checks")
        # corr_check_container = st.container(horizontal=True, horizontal_alignment="left", gap="large")

        # st.write("#### Filters")

        # axis_select_container = st.container(horizontal=True)

        # _ = axis_select_container.selectbox(
        #     label="Y Axis",
        #     options=["% of dependency changes", "# of dependency changes"],
        #     key="correlations_y_filter",
        # )

        # corr_header_container = st.container(horizontal=True)
        # corr_header_container.write("#### Plots")
        # show_corrs = corr_header_container.toggle(label="Show Correlation plots")

        # if show_corrs:
        #     ss["corr_check_stats"] = []
        #     for repo, workflows in ss["results_repos"].items():
        #         correlation_plot(repo, workflows)

        # passing_checks: int = len(list(filter(lambda x: x == "", ss["corr_check_stats"])))
        # failing_checks: list[int] = list(filter(lambda x: x != "", ss["corr_check_stats"]))

        # _ = corr_check_container.metric(label="Passing", value=passing_checks, width="content")
        # _ = corr_check_container.metric(label="Failing", value=len(failing_checks), help=f"{failing_checks if len(failing_checks) > 0 else ''}", width="content")
        # _ = corr_check_container.metric(label="Total", value=len(ss["corr_check_stats"]), width="content")
else:
    st.write("Please select at least one workflow")
