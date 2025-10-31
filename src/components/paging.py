import streamlit as st

from numpy.random import random_integers
from random import randint

from ..init.callbacks import change_page


ss = st.session_state

def make_paging_component(pages: int) -> None:
    paging_container = st.container(
        horizontal=True, 
        vertical_alignment="center", 
        horizontal_alignment="center",
        key=randint(0, 100000),
    )
    
    _ = paging_container.button(
        label=":material/first_page:",
        disabled=ss["curr_page_timelines"] == 1,
        on_click=change_page,
        kwargs={"where": 0},
        key=randint(0, 100000),
    )
    _ = paging_container.button(
        label=":material/keyboard_arrow_left:",
        disabled=ss["curr_page_timelines"] == 1,
        on_click=change_page,
        kwargs={"where": 1},
        key=randint(0, 100000),
    )
    _ = paging_container.html(f"""
        <div style='display: flex; justify-content: center; align-content: center'>
            <p style='text-align: center; margin: 0'>
                {ss["curr_page_timelines"]} of {pages}
            </p>
        </div>""",
        width="content",
    )
    _ = paging_container.button(
        label=":material/keyboard_arrow_right:",
        disabled=ss["curr_page_timelines"] == pages,
        on_click=change_page,
        kwargs={"where": 2},
        key=randint(0, 100000),
    )
    _ = paging_container.button(
        label=":material/last_page:",
        disabled=ss["curr_page_timelines"] == pages,
        on_click=change_page,
        kwargs={"where": 3, "max_pages": pages},
        key=randint(0, 100000),
    )
