import streamlit as st
import plotly.express as ex

from hashlib import sha256


def _correlation_check(values: dict[str, str]):
    actions_diff: list[int] = values["actions_diff"]
    actions_changes: list[int] = values["actions_changes"]
    non_user_changes: list[int] = [sum(x) for x in zip(values["non_user_action_upgrades"], values["non_user_action_downgrades"])]
    abs_diff: list[int] = values["dependencies_abs_diff"]
    shas: list[int] = values["shas"]
    
    return [
        s
        for x, y, z, i, s in zip(actions_diff, actions_changes, non_user_changes, abs_diff, shas)
        if i != 0 and abs(x) + abs(y) + abs(z) == 0
    ]
    

def compute_rug_pulls() -> dict[str, list[str]]:
    values = st.session_state["results_repos"]
    rug_pulled: dict[str, list[str]] = {
        "Commit": [],
        "Non User Changes": [],
        "Dep. Changes": [],
        "Vulnerable Dep. Changes": [],
        "Introduced Vulnerabilities": [],
    }
    
    for repo, workflows in values.items():
        for workflow, data in workflows.items():
            for index in range(len(data["shas"])):
                if (data["non_user_action_upgrades"][index] > 0 or data["non_user_action_downgrades"][index] < 0) \
                    and data["actions_changes"][index] == 0 \
                    and data["actions_diff"][index] <= 0 \
                    and data["vuln_dependencies_abs_diff"][index] > 0:
                        filepath = st.session_state["selected_repos"][repo].workflows[workflow].filepath
                        hash_digest = sha256(f"{filepath}".encode('utf-8')).hexdigest()
                        link = f"https://github.com/{repo}/commit/{data["shas"][index]}#diff-{hash_digest}"
                        
                        rug_pulled["Commit"].append(f"[{repo}/{workflow}/{data["shas"][index]}]({link}) :material/link:")
                        rug_pulled["Non User Changes"].append(
                            f"+{data["non_user_action_upgrades"][index]}/" +
                            f"{"-" if data["non_user_action_downgrades"][index] == 0 else ""}{data["non_user_action_downgrades"][index]}"
                        )
                        rug_pulled["Dep. Changes"].append(
                            f"{"+" if data["dependencies_abs_diff"][index] > 0 else ""}{data["dependencies_abs_diff"][index]}" +
                            f" ({"+" if data["dependencies_prop_diff"][index] > 0 else ""}{data["dependencies_prop_diff"][index]}%)"
                        )
                        rug_pulled["Vulnerable Dep. Changes"].append(
                            f"+{data["vuln_dependencies_abs_diff"][index]}" +
                            f" (+{data["vuln_dependencies_prop_diff"][index]}%)"
                        )
                        
                        indirect_deps = {
                            name: dependency
                            for name, dependency in st.session_state["selected_workflows"][repo][workflow].commits[data["shas"][index]].dependencies["indirect"].items()
                            if len(dependency.vulnerabilities) > 0
                        }
                        
                        if index > 0:
                            prev_indirect_deps = {
                                name: dependency
                                for name, dependency in st.session_state["selected_workflows"][repo][workflow].commits[data["shas"][index-1]].dependencies["indirect"].items()
                                if len(dependency.vulnerabilities) > 0
                            }
                            
                            deps_changes = set(indirect_deps.keys()) - set(prev_indirect_deps.keys())
                            new_vulns = {name: vuln["cvss"] for change in deps_changes for name, vuln in indirect_deps[change].vulnerabilities.items()}
                        else:
                            new_vulns = {name: vuln["cvss"] for change in indirect_deps.values() for name, vuln in change.vulnerabilities.items()}
                            
                        rug_pulled_vulns = ""
                        
                        for n, s in new_vulns.items():
                            rug_pulled_vulns += f"- {n} (CVSS {s})\n"
                
                        rug_pulled["Introduced Vulnerabilities"].append(rug_pulled_vulns)
    return rug_pulled


def correlation_plot(repo_name: str, workflows: dict[str, dict[str, str]]) -> None:
    y_filter = st.session_state["correlations_y_filter"]

    st.write(f"##### {repo_name} _({len(workflows)} workflows)_")

    workflows_container = st.container(gap="medium")

    for workflow, values in workflows.items():
        if len(values["shas"]) == 0: continue
        
        workflow_plots = workflows_container.container(gap="small")
        workflow_plots_title_container = workflow_plots.container(gap="small", horizontal=True, vertical_alignment="center")
        
        corr_check = _correlation_check(values)
        
        workflow_plots_title_container.write(f"###### {workflow} _({len(values['shas'])} commits)_")
        
        if len(corr_check) > 0:
            st.session_state["corr_check_stats"].append(f"{repo_name}/{workflow}")
            
            _ = workflow_plots_title_container.badge(
                label="Corr. Check",
                icon=":material/close:",
                color="red"
            )
            
            _ = workflow_plots_title_container.text(
                body="",
                help=f"Problematic commits: {[s for s in corr_check]}"
            )
        else:
            st.session_state["corr_check_stats"].append("")
            
            _ =  workflow_plots_title_container.badge(
                label="Corr. Check",
                icon=":material/check:",
                color="green"
            )

        col1, col2 = workflow_plots.columns(2)
        col3, col4 = workflow_plots.columns(2)
        col5, col6 = workflow_plots.columns(2)

        match y_filter:
            case "% of dependency changes":
                y_deps = values["dependencies_prop_diff"]
                y_vulns = values["vuln_dependencies_prop_diff"]
            case _:
                y_deps = values["dependencies_abs_diff"]
                y_vulns = values["vuln_dependencies_abs_diff"]

        fig1 = ex.scatter(
            x=values["actions_diff"],
            y=y_deps,
            color_discrete_sequence=["rgb(99,110,251)"],
            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig2 = ex.scatter(
            x=values["actions_diff"],
            y=y_vulns,
            color_discrete_sequence=["rgb(251,99,110)"],
            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig3 = ex.scatter(
            x=values["actions_changes"],
            y=y_deps,
            color_discrete_sequence=["rgb(99,110,251)"],
            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig4 = ex.scatter(
            x=values["actions_changes"],
            y=y_vulns,
            color_discrete_sequence=["rgb(251,99,110)"],
            hover_data={
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig5 = ex.scatter(
            x=[sum(x) for x in zip(values["non_user_action_upgrades"], values["non_user_action_downgrades"])],
            y=y_deps,
            color_discrete_sequence=["rgb(99,110,251)"],
            hover_data={
                "upgraded": values["non_user_action_upgrades"],
                "downgraded": values["non_user_action_downgrades"],
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        fig6 = ex.scatter(
            x=[sum(x) for x in zip(values["non_user_action_upgrades"], values["non_user_action_downgrades"])],
            y=y_vulns,
            color_discrete_sequence=["rgb(251,99,110)"],
            hover_data={
                "upgraded": values["non_user_action_upgrades"],
                "downgraded": values["non_user_action_downgrades"],
                "index": range(len(values["shas"])),
                "sha": values["shas"]
            },
        )
        
        labels_x = ["# added/removed Actions", "# user Action version changes", "# non-user upgraded(+)/downgraded(-) Actions"]
        
        for n, fig in enumerate([fig1, fig2, fig3, fig4, fig5, fig6]):
            label_y = y_filter
            label_x = labels_x[0]
            limit_y = max(abs(min(y_deps)), max(y_deps)) + 8
            limit_x = max(abs(min(values["actions_diff"])), max(values["actions_diff"])) + 1
            
            if (n+1) % 2 == 0:
                label_y = y_filter.replace("dependencies", "vulnerabilities").replace("dependency", "vulnerability")
                limit_y = max(abs(min(y_vulns)), max(y_vulns)) + 5
            
            if n > 1:
                limit_x = max(abs(min(values["actions_changes"])), max(values["actions_changes"])) + 2
                label_x = labels_x[1]
            if n > 3:
                changes = [sum(x) for x in zip(values["non_user_action_upgrades"], values["non_user_action_downgrades"])]
                limit_x = max(abs(min(changes)), max(changes)) + 2
                label_x = labels_x[2]
                
            if "%" in y_filter:
                limit_y = 1.4
            
            fig = fig.update_layout(showlegend=False, xaxis_title=label_x, yaxis_title=label_y)
            fig = fig.update_xaxes(range=[-limit_x, limit_x], showgrid=False, zerolinecolor="#E6EAF1")
            fig = fig.update_yaxes(range=[-limit_y, limit_y], showgrid=False, zerolinecolor="#E6EAF1")


        _ = col1.plotly_chart(figure_or_data=fig1, theme=None, key=f"{repo_name}-{workflow}-col1", on_select="rerun")
        _ = col2.plotly_chart(figure_or_data=fig2, theme=None, key=f"{repo_name}-{workflow}-col2", on_select="rerun")
        _ = col3.plotly_chart(figure_or_data=fig3, theme=None, key=f"{repo_name}-{workflow}-col3", on_select="rerun")
        _ = col4.plotly_chart(figure_or_data=fig4, theme=None, key=f"{repo_name}-{workflow}-col4", on_select="rerun")
        _ = col5.plotly_chart(figure_or_data=fig5, theme=None, key=f"{repo_name}-{workflow}-col5", on_select="rerun")
        _ = col6.plotly_chart(figure_or_data=fig6, theme=None, key=f"{repo_name}-{workflow}-col6", on_select="rerun")
