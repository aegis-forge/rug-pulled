from os.path import abspath, dirname, join

import streamlit as st

from src.components.rugpulls import make_gantt_charts, make_rug_pulls_component
from src.init.variables import init_session_variables

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

if len(ss["selected_workflows"]) == 0:
    ss["results_repos"] = {}
    
stats, gantts = st.tabs(["Statistics", "Gantt Charts"])

if len(ss["selected_workflows"]) > 0:
    with stats:
        make_rug_pulls_component()
    with gantts:
        make_gantt_charts()
else:
    st.write("Please select at least one workflow")
