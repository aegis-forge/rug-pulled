from datetime import datetime
from neotime import DateTime
from os import makedirs
from os.path import join, dirname, abspath
from pickle import load, dump, HIGHEST_PROTOCOL
from tqdm import tqdm

from models.db import Commit, Repository, Workflow
from .db import connect, get_workflow_commits, get_commit_dependencies


def repos2pickles():
    sess = connect()
    works = get_workflow_commits(sess)
    
    makedirs(join(dirname(abspath(__file__)), "../../repositories"), exist_ok=True)
    
    repositories: dict[str, Repository] = {}
    
    for workflow, commits in tqdm(works.items(), desc="Retrieving Workflows"):
        repo_name = '/'.join(workflow.split("/")[:2])
        workflow_name = workflow.split("/")[-1]
        
        if repo_name not in repositories:
            repositories[repo_name] = Repository(repo_name, {})
            
        if workflow_name not in repositories[repo_name].workflows:
            repositories[repo_name].workflows[workflow_name] = Workflow({})
        
        for commit in tqdm(sorted(commits, key=lambda el: el["date"]), leave=False, desc=f"Retrieving Commits for {workflow}"):
            date: DateTime = commit["date"]
            parsed = datetime(date.year, date.month, date.day, date.hour, date.minute, date.day)
            
            repositories[repo_name].workflows[workflow_name].commits[commit["name"]] = Commit(
                parsed,
                get_commit_dependencies(f"{workflow}/{commit['name']}", sess)
            )

    for name, repository in repositories.items():
        with open(join(dirname(abspath(__file__)), f"../../repositories/{name.replace('/', '::')}.pickle"), "wb") as file:
            dump(repository, file, protocol=HIGHEST_PROTOCOL)
            

def pickle2repo(file_name: str) -> Repository:
    with open(join(dirname(abspath(__file__)), f"../../repositories/{file_name}.pickle"), "rb") as file:
        return load(file)
