from altair.vegalite.v5.api import value
import streamlit as st

from datetime import datetime
from hashlib import sha256
from pandas import DataFrame
from scipy.stats import kendalltau

from ..models.neo import Dependency, Workflow


ss = st.session_state


def compute_dependencies(workflow: Workflow) -> dict[str, list[datetime] | list[int]]:
    dates: list[datetime] = []
    direct: list[int] = []
    direct_vuln: list[int] = []
    direct_dev: list[int] = []
    direct_dev_vuln: list[int] = []
    direct_opt: list[int] = []
    direct_opt_vuln: list[int] = []
    indirect: list[int] = []
    indirect_vuln: list[int] = []

    for commit in workflow.commits.values():
        dates.append(commit.date)

        indirect_deps = commit.dependencies["indirect"].values()
        vuln_indirect_deps = list(
            filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps)
        )

        direct.append(
            len(list(filter(lambda el: el.subtype == "direct", indirect_deps)))
        )
        direct_vuln.append(
            len(list(filter(lambda el: el.subtype == "direct", vuln_indirect_deps)))
        )
        direct_dev.append(
            len(list(filter(lambda el: el.subtype == "direct_dev", indirect_deps)))
        )
        direct_dev_vuln.append(
            len(list(filter(lambda el: el.subtype == "direct_dev", vuln_indirect_deps)))
        )
        direct_opt.append(
            len(list(filter(lambda el: el.subtype == "direct_opt", indirect_deps)))
        )
        direct_opt_vuln.append(
            len(list(filter(lambda el: el.subtype == "direct_opt", vuln_indirect_deps)))
        )
        indirect.append(
            len(list(filter(lambda el: el.subtype == "indirect", indirect_deps)))
        )
        indirect_vuln.append(
            len(list(filter(lambda el: el.subtype == "indirect", vuln_indirect_deps)))
        )

    return {
        "dates": dates,
        "direct": direct,
        "direct_vuln": direct_vuln,
        "direct_dev": direct_dev,
        "direct_dev_vuln": direct_dev_vuln,
        "direct_opt": direct_opt,
        "direct_opt_vuln": direct_opt_vuln,
        "indirect": indirect,
        "indirect_vuln": indirect_vuln,
    }


def compute_trend(workflow: Workflow, dependencies: bool = False) -> dict[str, float]:
    dates: list[float] = []
    count_vuln: list[int] = []

    for commit in sorted(workflow.commits.values(), key=lambda x: x.date):
        indirect_deps = commit.dependencies["indirect"].values()
        vuln_indirect_deps = list(
            filter(lambda el: len(el.vulnerabilities) > 0, indirect_deps)
        )

        if len(vuln_indirect_deps) == 0 and len(indirect_deps) == 0:
            continue

        dates.append(commit.date.timestamp())
        count_vuln.append(
            len(indirect_deps) if dependencies else len(vuln_indirect_deps)
        )

    if len(count_vuln) <= 1:
        return {"tau": 0.0, "pvalue": 0.0}

    tau, pvalue = kendalltau(dates, count_vuln)

    return {"tau": tau, "pvalue": pvalue}


def compute_trend_category(
    tau: float, pvalue: float, threshold: float
) -> dict[str, str]:
    trend_type = ":material/equal:"
    trend_color = "gray"

    if pvalue <= threshold and pvalue != 0:
        if -1 <= tau < -0.5:
            trend_type = ":material/keyboard_double_arrow_down:"
            trend_color = "green"
        elif -0.5 <= tau < 0:
            trend_type = ":material/keyboard_arrow_down:"
            trend_color = "green"
        elif 0 < tau <= 0.5:
            trend_type = ":material/keyboard_arrow_up:"
            trend_color = "red"
        elif 0.5 < tau <= 1:
            trend_type = ":material/keyboard_double_arrow_up:"
            trend_color = "red"

    return {
        "type": trend_type,
        "color": trend_color,
    }


def _compute_rug_pulled_dependencies(
    workflows: list[Workflow],
) -> dict[str, dict[str, Dependency]]:
    rug_pulled_dependencies: dict[str, dict[str, Dependency]] = {}

    for workflow_name, workflow in workflows.items():
        pos = -1
        prev_actions: int = -1
        vuln_prev_dependencies: dict[str, Dependency] = {}
        prev_user_versions: dict[str, Dependency] = {}

        for commit_sha, commit in workflow.commits.items():
            changes = 0
            non_user_upgrades = 0
            non_user_downgrades = 0

            actions = commit.dependencies["direct"]
            vuln_indirect_deps = {
                key: value
                for key, value in commit.dependencies["indirect"].items()
                if len(value.vulnerabilities) > 0
            }

            for name, dep in commit.dependencies["direct"].items():
                if name in prev_user_versions:
                    prev = prev_user_versions[name]
                    changes += 1 if dep.version != prev.version else 0

                    if dep.date and prev.date:
                        if dep.version != prev.version:
                            non_user_upgrades += 0
                            non_user_downgrades -= 0

                        non_user_upgrades += 1 if dep.date > prev.date else 0
                        non_user_downgrades -= 1 if dep.date < prev.date else 0

                prev_user_versions[name] = dep

            vuln_abs_diff = 0

            if len(vuln_prev_dependencies) != 0:
                vuln_abs_diff = len(vuln_indirect_deps) - len(vuln_prev_dependencies)

            if pos != -1:
                if (
                    (non_user_upgrades > 0 or non_user_downgrades < 0)
                    and changes == 0
                    and len(actions) - len(prev_actions) <= 0
                    and vuln_abs_diff > 0
                ):
                    rug_pulled_dependencies[f"{workflow_name}::{commit_sha}"] = {
                        key: value
                        for key, value in vuln_indirect_deps.items()
                        if key not in vuln_prev_dependencies
                    }

            vuln_prev_dependencies = vuln_indirect_deps
            prev_actions = actions
            pos += 1

    return rug_pulled_dependencies


def compute_rug_pulls(page: int = 1) -> DataFrame:
    values = st.session_state["results_repos"]
    rug_pulls: dict[str, list[str]] = {
        "#": [],
        "Commit": [],
        "Non User Changes": [],
        "Actions": [],
        "Introduced Vulnerabilities": [],
    }

    for repo_name, workflows in ss["selected_workflows"].items():
        rug_pulled_dependencies = _compute_rug_pulled_dependencies(workflows)

        for workflow_name, deps in rug_pulled_dependencies.items():
            sorted_commits = sorted(
                workflows[workflow_name.split("::")[0]].commits.items(),
                key=lambda x: x[1].date,
            )

            start = [el[0] for el in sorted_commits].index(workflow_name.split("::")[1])

            for commit in [el[0] for el in sorted_commits][start:]:
                pass

    return DataFrame()

    # curr_ind = 1
    # for repo, workflows in values.items():
    #     for workflow, data in workflows.items():
    #         for index in range(len(data["shas"])):
    #             if (
    #                 (
    #                     data["non_user_action_upgrades"][index] > 0
    #                     or data["non_user_action_downgrades"][index] < 0
    #                 )
    #                 and data["actions_changes"][index] == 0
    #                 and data["actions_diff"][index] <= 0
    #                 and data["vuln_dependencies_abs_diff"][index] > 0
    #             ):
    #                 filepath = (
    #                     st.session_state["selected_repos"][repo]
    #                     .workflows[workflow]
    #                     .filepath
    #                 )
    #                 hash_digest = sha256(f"{filepath}".encode("utf-8")).hexdigest()
    #                 link = f"https://github.com/{repo}/commit/{data['shas'][index]}#diff-{hash_digest}"

    #                 rug_pulls["Commit"].append(
    #                     f"[{repo}/{workflow}/{data['shas'][index]}]({link}) :material/link:"
    #                 )
    #                 rug_pulls["Non User Changes"].append(
    #                     f"+{data['non_user_action_upgrades'][index]}/"
    #                     + f"{data['non_user_action_downgrades'][index]}"
    #                 )
    #                 # rug_pulls["Dep. Changes"].append(
    #                 #     f"{'+' if data['dependencies_abs_diff'][index] > 0 else ''}{data['dependencies_abs_diff'][index]}"
    #                 #     + f" ({'+' if data['dependencies_prop_diff'][index] > 0 else ''}{data['dependencies_prop_diff'][index]}%)"
    #                 # )
    #                 # rug_pulls["Vulnerable Dep. Changes"].append(
    #                 #     f"+{data['vuln_dependencies_abs_diff'][index]}"
    #                 #     + f" (+{data['vuln_dependencies_prop_diff'][index]}%)"
    #                 # )

    #                 indirect_deps = {
    #                     name: dependency
    #                     for name, dependency in st.session_state["selected_workflows"][
    #                         repo
    #                     ][workflow]
    #                     .commits[data["shas"][index]]
    #                     .dependencies["indirect"]
    #                     .items()
    #                     if len(dependency.vulnerabilities) > 0
    #                 }

    #                 if index > 0:
    #                     prev_indirect_deps = {
    #                         name: dependency
    #                         for name, dependency in st.session_state[
    #                             "selected_workflows"
    #                         ][repo][workflow]
    #                         .commits[data["shas"][index - 1]]
    #                         .dependencies["indirect"]
    #                         .items()
    #                         if len(dependency.vulnerabilities) > 0
    #                     }

    #                     deps_changes = set(indirect_deps.keys()) - set(
    #                         prev_indirect_deps.keys()
    #                     )

    #                     new_vulns = {
    #                         name: vuln["cvss"]
    #                         for change in deps_changes
    #                         for name, vuln in indirect_deps[
    #                             change
    #                         ].vulnerabilities.items()
    #                     }
    #                 else:
    #                     new_vulns = {
    #                         name: vuln["cvss"]
    #                         for change in indirect_deps.values()
    #                         for name, vuln in change.vulnerabilities.items()
    #                     }

    #                 rug_pulled_vulns = ""

    #                 for n, s in new_vulns.items():
    #                     rug_pulled_vulns += (
    #                         f"- {n} (CVSS **:{_compute_cvss_color(s)}[{s}]**)\n"
    #                     )

    #                 rug_pulls["Introduced Vulnerabilities"].append(rug_pulled_vulns)
    #                 rug_pulls["#"].append(curr_ind)

    #                 curr_ind += 1
    # return DataFrame(rug_pulls).set_index("#")


def _compute_cvss_color(cvss: float) -> str:
    color = "grey"

    if 0.0 < cvss < 4.0:
        color = "blue"
    elif 4.0 <= cvss < 7.0:
        color = "orange"
    elif 7.0 <= cvss < 9.0:
        color = "red"
    elif 9.0 <= cvss <= 10.0:
        color = "violet"

    return color
