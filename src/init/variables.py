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
        
    if "rug_pulls" not in st.session_state:
        st.session_state["rug_pulls"] = {}
        
    if "cut_rug_pulls" not in st.session_state:
        st.session_state["cut_rug_pulls"] = {}
        
    if "corr_check_stats" not in st.session_state:
        st.session_state["corr_check_stats"] = []
        
    if "curr_page_timelines" not in st.session_state:
        st.session_state["curr_page_timelines"] = 1
        
    if "curr_page_rug_pulls" not in st.session_state:
        st.session_state["curr_page_rug_pulls"] = 1
