import streamlit as st

from streamlit.delta_generator import DeltaGenerator


def make_metrics_components(
    labels: list[str],
    values: list[int],
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
        colors = ["black" for _ in range(len(labels))]

    for label, value, color in zip(labels, values, colors):
        _ = container.metric(
            label=f"**:{color}[{label}]**",
            value=value,
            width="content",
        )
