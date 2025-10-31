import streamlit as st

from ..helpers.repos import get_repo_names


def init_session_variables() -> None:
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
        
    if "corr_check_stats" not in st.session_state:
        st.session_state["corr_check_stats"] = []
        
    if "curr_page_timelines" not in st.session_state:
        st.session_state["curr_page_timelines"] = 1
