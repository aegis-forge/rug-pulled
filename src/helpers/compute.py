from datetime import datetime
from hashlib import sha256

import streamlit as st
from pandas import DataFrame
from scipy.stats import kendalltau

from ..models.neo import Dependency, Workflow
from ..models.rugs import Fix, Rugpull

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
    repo_name: str, workflows: dict[str, Workflow]
) -> list[Rugpull]:
    rug_pulled_actions: list[Rugpull] = []

    for workflow_name, workflow in workflows.items():
        pos = -1
        prev_commit_sha: str = ""
        vuln_prev_dependencies: dict[str, Dependency] = {}
        prev_user_versions: dict[str, Dependency] = {}

        for commit_sha, commit in workflow.commits.items():
            vuln_indirect_deps = {
                key: dep
                for key, dep in commit.dependencies["indirect"].items()
                if len(dep.vulnerabilities) > 0
            }

            if pos == -1:
                vuln_prev_dependencies = vuln_indirect_deps
                prev_commit_sha = commit_sha
                pos += 1

                continue

            for name, dep in commit.dependencies["direct"].items():
                if name not in prev_user_versions:
                    prev_user_versions[name] = dep

                prev = prev_user_versions[name]

                if not dep.date or not prev.date:
                    continue

                if dep.version == prev.version and dep.date != prev.date:
                    current_action_vulns = {
                        key: dep
                        for key, dep in vuln_indirect_deps.items()
                        if dep.parent == name
                    }

                    prev_action_vulns = {
                        key: dep
                        for key, dep in vuln_prev_dependencies.items()
                        if dep.parent == name
                    }

                    new_vulnerable_deps = {
                        key: dep
                        for key, dep in current_action_vulns.items()
                        if key not in prev_action_vulns
                    }

                    if len(new_vulnerable_deps) == 0:
                        continue

                    filepath = workflow.filepath
                    hash_digest: str = sha256(f"{filepath}".encode("utf-8")).hexdigest()
                    link_from = f"https://github.com/{repo_name}/commit/{prev_commit_sha}#diff-{hash_digest}"
                    link_to = f"https://github.com/{repo_name}/commit/{commit_sha}#diff-{hash_digest}"

                    rug_pulled_actions.append(
                        Rugpull(
                            location=f"{repo_name}/{workflow_name}/{commit_sha}",
                            from_commit=f"{repo_name}/{workflow_name}/{prev_commit_sha}",
                            links=(link_from, link_to),
                            action=(name, dep),
                            vulnerabilities=new_vulnerable_deps,
                            introduced=dep.date,
                            downgrade=dep.date < prev.date,
                        )
                    )

                prev_user_versions[name] = dep

            vuln_prev_dependencies = vuln_indirect_deps
            prev_commit_sha = commit_sha
            pos += 1

        for rug_pull in rug_pulled_actions:
            if (
                "/".join(rug_pull.location.split("/")[:3])
                != f"{repo_name}/{workflow_name}"
            ):
                break

            shas_sorted = sorted(workflow.commits.items(), key=lambda x: x[1].date)
            shas = [item[0] for item in shas_sorted]
            begin = shas.index(rug_pull.location.split("/")[-1]) + 1

            for commit in shas_sorted[begin:]:
                if rug_pull.fix:
                    break

                vuln_indirect_deps = {
                    key: dep
                    for key, dep in commit[1].dependencies["indirect"].items()
                    if len(dep.vulnerabilities) > 0
                }

                curr_action_vulns = {
                    key: dep
                    for key, dep in vuln_indirect_deps.items()
                    if dep.parent == rug_pull.action[0]
                }

                if rug_pull.action[0] not in commit[1].dependencies["direct"]:
                    rug_pull.fix = Fix(
                        sha=commit[0],
                        version=None,
                        date=commit[1].date,
                        ttf=commit[1].date - rug_pull.introduced,
                        who="Maintainer",
                    )

                    continue

                curr_action = commit[1].dependencies["direct"][rug_pull.action[0]]
                vuln_action = rug_pull.action[1]

                if not curr_action.date or not vuln_action.date:
                    continue

                if (
                    vuln_action.date == curr_action.date
                    and vuln_action.version == curr_action.version
                ):
                    continue

                actions_diff = [
                    dep
                    for dep in rug_pull.vulnerabilities.keys()
                    if dep in curr_action_vulns
                ]

                who = (
                    "Action"
                    if vuln_action.version == curr_action.version
                    else "Workflow"
                )
                date = curr_action.date if who == "Action" else commit[1].date

                if len(actions_diff) == 0:
                    rug_pull.fix = Fix(
                        sha=commit[0],
                        version=curr_action.version,
                        date=date,
                        ttf=date - rug_pull.introduced,
                        who=who,
                    )

    return rug_pulled_actions


def compute_rug_pulls() -> DataFrame:
    rug_pulls: dict[str, list[str]] = {
        "#": [],
        "Action": [],
        "Commit": [],
        "Date(s)": [],
        "Introduced Vulnerabilities": [],
        "Fixed By": [],
        "TTF (days)": [],
    }

    ind = 1

    for repo_name, workflows in ss["selected_workflows"].items():
        for rug_pull in sorted(
            _compute_rug_pulled_dependencies(repo_name, workflows),
            key=lambda x: x.location,
        ):
            rug_pulls["#"].append(str(ind))
            rug_pulls["Action"].append(
                f"{rug_pull.action[0]}@{rug_pull.action[1].version}"
                + f"{':red[:material/arrow_downward:]' if rug_pull.downgrade else ''}"
            )
            rug_pulls["Introduced Vulnerabilities"].append(
                "\n".join(
                    [
                        f"- **{dep_name}**: ({vuln_name} - CVSS: "
                        + f":{_compute_cvss_color(vuln['cvss'])}"
                        + f"[**{vuln['cvss']}**])"
                        for dep_name, dep in rug_pull.vulnerabilities.items()
                        for vuln_name, vuln in dep.vulnerabilities.items()
                    ]
                )
            )
            rug_pulls["Date(s)"].append(
                f":red[{rug_pull.introduced.strftime('%d %b %Y %H:%M:%S')}]\n\n"
                + f"{
                    f':green[{rug_pull.fix.date.strftime("%d %b %Y %H:%M:%S")}]'
                    if rug_pull.fix
                    else ''
                }"
            )
            rug_pulls["Commit"].append(
                f"{'/'.join(rug_pull.from_commit.split('/')[0:-1])}\n\n"
                + f"[{rug_pull.from_commit.split('/')[-1][:7]}"
                + " :material/arrow_forward: "
                + f"{rug_pull.location.split('/')[-1][:7]}]"
                + f"({rug_pull.links[1]}) :material/open_in_new:"
            )
            rug_pulls["Fixed By"].append(
                f"{rug_pull.fix.who + ' Maint.' if rug_pull.fix else '—'}"
                + f"{
                    ' (Removed)'
                    if rug_pull.fix and not rug_pull.fix.version
                    else ' (' + rug_pull.fix.version + ')'
                    if rug_pull.fix and rug_pull.fix.who != 'Action'
                    else ''
                }"
            )
            rug_pulls["TTF (days)"].append(
                rug_pull.fix.ttf.days if rug_pull.fix else "—"
            )

            ind += 1

    return DataFrame(rug_pulls).set_index("#")


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
