import streamlit as st

from random import randint

from ..init.callbacks import change_page


ss = st.session_state

def make_paging_component(pages: int, key: str) -> None:
    paging_container = st.container(
        horizontal=True, 
        vertical_alignment="center", 
        horizontal_alignment="center",
        key=randint(0, 100000),
    )
    
    _ = paging_container.button(
        label=":material/first_page:",
        disabled=ss[key] == 1,
        on_click=change_page,
        kwargs={"key": key, "where": 0},
        key=randint(0, 100000),
    )
    _ = paging_container.button(
        label=":material/keyboard_arrow_left:",
        disabled=ss[key] == 1,
        on_click=change_page,
        kwargs={"key": key, "where": 1},
        key=randint(0, 100000),
    )
    _ = paging_container.html(f"""
        <div style='display: flex; justify-content: center; align-content: center'>
            <p style='text-align: center; margin: 0'>
                {ss[key]} of {pages}
            </p>
        </div>""",
        width="content",
    )
    _ = paging_container.button(
        label=":material/keyboard_arrow_right:",
        disabled=ss[key] == pages,
        on_click=change_page,
        kwargs={"key": key, "where": 2},
        key=randint(0, 100000),
    )
    _ = paging_container.button(
        label=":material/last_page:",
        disabled=ss[key] == pages,
        on_click=change_page,
        kwargs={"key": key, "where": 3, "max_pages": pages},
        key=randint(0, 100000),
    )
