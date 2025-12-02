from json import dump, load
from os.path import abspath, dirname, isfile, join

import streamlit as st
from dotenv import dotenv_values
from tqdm import tqdm

from ..helpers.queries import connect, get_repository_workflows, get_workflow_commits

ss = st.session_state


def options_select():
    if "selected_repos_options" not in ss or "selected_workflows_options" not in ss:
        return

    session = connect(dotenv_values(join(dirname(abspath(__file__)), "../../.env")))

    if "All" in ss["selected_repos_options"]:
        ss["selected_repos_options"] = ["All"]
        ss["max_repo_selections"] = 1

        workflows = join(dirname(abspath(__file__)), "../../data/workflows.json")
        commits = join(dirname(abspath(__file__)), "../../data/commits.json")

        if isfile(workflows):
            with open(workflows) as file:
                ss["selected_workflows"] = load(file)

            with open(commits) as file:
                ss["selected_commits"] = load(file)

            return

        workflow_names: dict[str, list[str]] = {}
        commit_names: dict[str, list[str]] = {}

        for repo in tqdm(ss["repo_names"]):
            res = get_repository_workflows(repo, session)

            if list(res.keys()) == 0:
                continue

            workflow_names[repo] = list(res.keys())

            for workflow in list(res.keys()):
                commitss = [
                    commit[0]
                    for commit in get_workflow_commits(repo + "/" + workflow, session)
                ]
                
                if len(commitss) == 0:
                    continue
                
                commit_names[workflow] = commitss

        with open(workflows, "w") as file:
            dump(workflow_names, file)

        with open(commits, "w") as file:
            dump(commit_names, file)
    else:
        ss["max_repo_selections"] = len(ss["repo_names"])

    # selected_options = ss["selected_repos_options"]
    # repos = selected_options if "All" not in selected_options else ss["repo_names"]

    # ss["selected_repos"] = {}
    # ss["current_workflows"] = []
    # ss["selected_workflows"] = {}

    # for repo in repos:
    #     repo_obj = pickle2repo(f"{repo.replace('/', '::')}")
    #     ss["selected_repos"][repo] = repo_obj

    #     if len(repos) > 1:
    #         ss["selected_workflows"][repo] = repo_obj.workflows

    #     ss["current_workflows"].extend(list(repo_obj.workflows.keys()))

    # ss["current_workflows"].sort()


def get_workflows():
    repo_name = list(ss["selected_repos"].keys())[0]
    workflow_names = ss["selected_repos"][repo_name].workflows.keys()

    ss["selected_workflows"] = {repo_name: {}}

    for workflow in ss["selected_workflows_options"]:
        if workflow in workflow_names:
            ss["selected_workflows"][repo_name][workflow] = ss["selected_repos"][
                repo_name
            ].workflows[workflow]


def change_page(key: str, where: int, max_pages: int = 0):
    match where:
        case 0:
            ss[key] = 1
        case 1:
            ss[key] -= 1
        case 2:
            ss[key] += 1
        case 3:
            ss[key] = max_pages
        case _:
            return
