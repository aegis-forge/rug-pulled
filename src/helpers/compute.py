from ast import literal_eval
from datetime import datetime
from hashlib import sha256
from os.path import abspath, dirname, isfile, join
from typing import Any

import streamlit as st
from dotenv import dotenv_values
from numpy import nan
from pandas import DataFrame, read_csv
from scipy.stats import kendalltau
from tqdm import tqdm

from ..helpers.queries import connect, get_first_fixed_commit, is_dependency_fixable
from ..helpers.repos import pickle2repo
from ..models.neo import Dependency, Repository, Workflow
from ..models.rugs import ActualFix, PotentialFix, Rugpull

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
    trend_type = "equal"
    trend_color = "gray"

    if pvalue <= threshold and pvalue != 0:
        if -1 <= tau < -0.5:
            trend_type = "keyboard_double_arrow_down"
            trend_color = "green"
        elif -0.5 <= tau < 0:
            trend_type = "keyboard_arrow_down"
            trend_color = "green"
        elif 0 < tau <= 0.5:
            trend_type = "keyboard_arrow_up"
            trend_color = "red"
        elif 0.5 < tau <= 1:
            trend_type = "keyboard_double_arrow_up"
            trend_color = "red"

    return {
        "type": trend_type,
        "color": trend_color,
    }


def _compute_rug_pulled_dependencies(
    repo_name: str,
    workflows: dict[str, Workflow],
) -> list[Rugpull]:
    rug_pulled_actions: list[Rugpull] = []
    session = connect(dotenv_values(join(dirname(abspath(__file__)), "../../.env")))

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
                continue

            workflow = workflows[rug_pull.location.split("/")[2]]
            sorted_workflows = sorted(workflow.commits.values(), key=lambda x: x.date)
            last_date = sorted_workflows[-1].date

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

                direct_versions = [
                    (direct.version, direct.version_type)
                    for name, direct in commit[1].dependencies["direct"].items()
                    if name == rug_pull.action[0]
                ]

                if len(direct_versions) == 0:
                    rug_pull.fix = ActualFix(
                        sha=commit[0],
                        version=[],
                        version_type=None,
                        date=commit[1].date,
                        ttx=commit[1].date - rug_pull.introduced,
                        who="Workflow",
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
                    rug_pull.fix = ActualFix(
                        sha=commit[0],
                        version=[curr_action.version],
                        version_type=curr_action.version_type,
                        date=date,
                        ttx=date - rug_pull.introduced,
                        who=who,
                    )

            if not rug_pull.fix:
                fix = get_first_fixed_commit(
                    action=rug_pull.action[0],
                    deps=list(rug_pull.vulnerabilities.keys()),
                    date=rug_pull.introduced,
                    session=session,
                )

                if fix and fix[0] < last_date:
                    date = datetime(
                        fix[0].year,
                        fix[0].month,
                        fix[0].day,
                        fix[0].hour,
                        fix[0].minute,
                        fix[0].second,
                    )

                    if rug_pull.action[1].version in fix[1]:
                        rug_pull.fix = ActualFix(
                            sha=fix[2],
                            version=[rug_pull.action[1].version],
                            version_type=rug_pull.action[1].version_type,
                            date=date,
                            ttx=date - rug_pull.introduced,
                            who="Action",
                        )
                    else:
                        rug_pull.fix = PotentialFix(
                            sha=fix[2],
                            date=date,
                            versions=fix[1],
                            ttpf=date - rug_pull.introduced,
                        )
                else:
                    fixable_deps_dates = [
                        is_dependency_fixable(dep_name, dep.version)
                        for dep_name, dep in rug_pull.vulnerabilities.items()
                    ]

                    if None not in fixable_deps_dates and len(fixable_deps_dates) > 0:
                        fixable_deps_date = sorted(fixable_deps_dates)[-1]

                        if rug_pull.introduced < fixable_deps_date < last_date:
                            rug_pull.fix = PotentialFix(
                                sha="",
                                date=fixable_deps_date,
                                versions=[],
                                ttpf=fixable_deps_date - rug_pull.introduced,
                                dependencies=True,
                            )

    return rug_pulled_actions


def compute_rug_pulls() -> DataFrame:
    filepath = join(dirname(abspath(__file__)), "../../data/rug_pulls.csv")

    if isfile(filepath):
        df = read_csv(
            filepath,
            parse_dates=["date", "elapsed", "fix_date"],
            date_format="%Y-%m-%d %H-%M-%S",
        ).set_index("#")

        df["elapsed"] = df["elapsed"].map(int)
        df["vulns_list"] = df["vulns_list"].apply(lambda x: literal_eval(x))
        df["vulns_severities"] = df["vulns_severities"].apply(lambda x: literal_eval(x))
        df["fix_version"] = df["fix_version"].apply(lambda x: literal_eval(x))
        df["date"] = df["date"].astype("datetime64[s]")
        df["fix_date"] = df["fix_date"].astype("datetime64[s]")
        df["last"] = df["last"].astype("datetime64[s]")

        return df

    rug_pulls: dict[str, list[Any]] = {
        "#": [],
        "action": [],
        "version": [],
        "version_type": [],
        "version_used": [],
        "date": [],
        "repo": [],
        "workflow": [],
        "hash": [],
        "vulns_list": [],
        "vulns_severities": [],
        "last": [],
        "elapsed": [],
        "fix_category": [],
        "fix_date": [],
        "fix_actor": [],
        "fix_version": [],
        "fix_v_type": [],
        "fix_hash": [],
        "ttx": [],
        "ttpf": [],
    }

    index = 0

    for repo_name, workflows_raw in tqdm(ss["selected_workflows"].items()):
        repo: Repository = pickle2repo(f"{repo_name.replace('/', '::')}")
        workflows: dict[str, Workflow] = {
            name: repo.workflows[name]
            for name in workflows_raw
            if name in repo.workflows
        }

        rug_pulls_raw = _compute_rug_pulled_dependencies(repo_name, workflows)

        for rug_pull in rug_pulls_raw:
            fix = rug_pull.fix
            fixed = type(rug_pull.fix) is ActualFix
            p_fix = type(rug_pull.fix) is PotentialFix

            vulnerable_deps = [
                f"{dep_name}@v.{dep.version} - {dep.subtype}"
                for dep_name, dep in rug_pull.vulnerabilities.items()
            ]
            
            vulnerable_severities = [
                f"{dep_name} // {vuln_name} // {vuln["cvss"]}"
                for dep_name, dep in rug_pull.vulnerabilities.items()
                for vuln_name, vuln in dep.vulnerabilities.items()
            ]

            workflow = workflows[rug_pull.location.split("/")[2]]
            sorted_workflows = sorted(workflow.commits.values(), key=lambda x: x.date)
            last_date = sorted_workflows[-1].date

            rug_pulls["#"].append(index + 1)
            rug_pulls["action"].append(rug_pull.action[0])
            rug_pulls["version"].append(rug_pull.action[1].version)
            rug_pulls["version_type"].append(rug_pull.action[1].version_type)
            rug_pulls["version_used"].append(rug_pull.action[1].uses)
            rug_pulls["date"].append(rug_pull.introduced)
            rug_pulls["repo"].append("/".join(rug_pull.location.split("/")[:2]))
            rug_pulls["workflow"].append(rug_pull.location.split("/")[2])
            rug_pulls["hash"].append(rug_pull.location.split("/")[-1])
            rug_pulls["vulns_list"].append(vulnerable_deps)
            rug_pulls["vulns_severities"].append(vulnerable_severities)
            rug_pulls["elapsed"].append((last_date - rug_pull.introduced).days)
            rug_pulls["last"].append(last_date)
            rug_pulls["fix_category"].append(rug_pull.get_fix_category())
            rug_pulls["fix_date"].append(fix.date if fix else nan)
            rug_pulls["fix_actor"].append(fix.who if fixed else nan)
            rug_pulls["fix_version"].append(fix.versions if fixed else [])
            rug_pulls["fix_v_type"].append(fix.version_type if fixed else nan)
            rug_pulls["fix_hash"].append(fix.sha if fix else nan)
            rug_pulls["ttx"].append(fix.ttx.days if fixed else nan)
            rug_pulls["ttpf"].append(fix.ttpf.days if p_fix else nan)

            index += 1

    df = DataFrame(rug_pulls).set_index("#")
    df.to_csv(filepath)

    return df
