import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def make_metrics_components(
    labels: list[str],
    values: list[int | float],
    colors: list[str] | None = None,
    icons: bool | None = None,
    container: DeltaGenerator | None = None,
) -> None:
    if len(labels) != len(values):
        raise Exception("`labels` and `values` must be of the same length")

    if colors and (len(colors) != len(values) or len(colors) != len(labels)):
        raise Exception("`colors`, `labels`, and `values` must be of the same length")

    if not container:
        container = st.container(
            horizontal=True,
            vertical_alignment="center",
            horizontal_alignment="left",
            gap="large",
        )

    if not colors:
        colors = ["" for _ in range(len(labels))]

    for label, value, color in zip(labels, values, colors):
        label = label if not icons else f"""
            <span
                role="img"
                aria-label="{label} icon"
                style="
                    display: inline-block;
                    font-family: Material Symbols Rounded;
                    font-weight: 400;
                    user-select: none;
                    vertical-align: bottom;
                    white-space: nowrap;
                    overflow-wrap: normal;
                "
            >
                {label}
            </span>
        """
        
        container.html(
            f"""
            <strong style="color: {color}">{label}</strong>
            <p style="font-size: 40px !important; margin-top: -8px !important">
                {value}
            </p>
            """,
            width="content",
        )
