from plotly.io.orca import config
import streamlit as st
import plotly.express as ex

from models.db import Workflow


def _compute_vals(workflows: dict[str, Workflow]) -> dict[str, dict[str, list[float]]]:
    results: dict[str, dict[str, list[float]]] = {}

    for workflow_name, workflow in workflows.items():
        shas: list[str] = []
        actions: list[int] = []
        dependencies_prop_diff: list[float] = []
        vuln_dependencies_prop_diff: list[float] = []

        prev_dependencies_count = 0
        vuln_prev_dependencies_count = 0

        for commit_name, commit in workflow.commits.items():
            shas.append(commit_name)

            direct_deps = commit.dependencies["direct"].values()
            indirect_deps = commit.dependencies["indirect"].values()
            vuln_indirect_deps = list(
                filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps)
            )

            actions.append(len(direct_deps))

            dependencies_diff = 1.0
            vuln_dependencies_diff = 1.0

            if prev_dependencies_count != 0:
                dependencies_diff = round(
                    (len(indirect_deps) - prev_dependencies_count)
                    / prev_dependencies_count,
                    2,
                )
            elif prev_dependencies_count == 0 and len(indirect_deps) == 0:
                dependencies_diff = 0

            if vuln_prev_dependencies_count != 0:
                vuln_dependencies_diff = round(
                    (len(vuln_indirect_deps) - vuln_prev_dependencies_count)
                    / vuln_prev_dependencies_count,
                    2,
                )
            elif vuln_prev_dependencies_count == 0 and len(vuln_indirect_deps) == 0:
                vuln_dependencies_diff = 0

            dependencies_prop_diff.append(dependencies_diff)
            prev_dependencies_count = len(indirect_deps)
            vuln_dependencies_prop_diff.append(vuln_dependencies_diff)
            vuln_prev_dependencies_count = len(vuln_indirect_deps)

        actions_diff = [actions[0]] + [
            actions[i] - actions[i - 1] for i in range(1, len(actions))
        ]

        results[workflow_name] = {
            "shas": shas,
            "actions_diff": actions_diff,
            "dependencies_prop_diff": dependencies_prop_diff,
            "vuln_dependencies_prop_diff": vuln_dependencies_prop_diff,
        }

    return results


def correlation_plot(repo_name: str, workflows: dict[str, Workflow]) -> None:
    results = _compute_vals(workflows)

    st.write(f"##### {repo_name}")

    workflows_container = st.container(gap="medium")

    for workflow, values in results.items():
        workflow_plots = workflows_container.container(gap="small")
        workflow_plots.write(f"###### {workflow}")

        col1, col2 = workflow_plots.columns(2)
        # col3, col4 = workflow_plots.columns(2)

        limit = max(abs(min(values["actions_diff"])), max(values["actions_diff"]))

        fig1 = ex.scatter(
            x=values["actions_diff"],
            y=values["dependencies_prop_diff"],
            color_discrete_sequence=["rgb(99,110,251)"],

            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig2 = ex.scatter(
            x=values["actions_diff"],
            y=values["vuln_dependencies_prop_diff"],
            color_discrete_sequence=["rgb(251,99,110)"],
            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )

        fig1 = fig1.update_layout(showlegend=False, xaxis_title="# added/removed Actions", yaxis_title="% of dependency changes")
        fig1 = fig1.update_xaxes(range=[-limit-1, limit+1], showgrid=False, zerolinecolor="#E6EAF1")
        fig1 = fig1.update_yaxes(range=[-1.4, 1.4], showgrid=False, zerolinecolor="#E6EAF1")

        fig2 = fig2.update_layout(showlegend=False, xaxis_title="# added/removed Actions", yaxis_title="% of vulnerability changes")
        fig2 = fig2.update_xaxes(range=[-limit-1, limit+1], showgrid=False, zerolinecolor="#E6EAF1")
        fig2 = fig2.update_yaxes(range=[-1.4, 1.4], showgrid=False, zerolinecolor="#E6EAF1")

        _ = col1.plotly_chart(
            figure_or_data=fig1,
            theme=None,
            key=f"{repo_name}-{workflow.split('.')[0]}-deps",
        )
        _ = col2.plotly_chart(
            figure_or_data=fig2,
            theme=None,
            key=f"{repo_name}-{workflow.split('.')[0]}-vulns",
        )
