import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def make_metrics_components(
    labels: list[str],
    values: list[int | float],
    colors: list[str] | None = None,
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
        colored_string = f":{color}[{label}]" if color != "" else label

        _ = container.metric(
            label=f"**{colored_string}**",
            value=value,
            width="content",
        )
