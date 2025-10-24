from datetime import datetime
from pathlib import Path
from neo4j.exceptions import ServiceUnavailable
from neotime import DateTime
from os import listdir, mkdir
from os.path import join, dirname, abspath, isdir
from pickle import load, dump, HIGHEST_PROTOCOL
from tqdm import tqdm

from ..models.db import Commit, Repository, Workflow
from .db import connect, get_all_repositories, get_repository_workflows, get_workflow_commits, get_commit_dependencies


def repos2pickles(env: dict[str, str]):
    sess = connect(env)
    
    if sess is None and env["MODE"] == "debug": return
    elif not sess: raise ServiceUnavailable
    
    pickles_dir = join(dirname(abspath(__file__)), "../../repositories")
    
    if not isdir(pickles_dir): mkdir(pickles_dir)
    if len(listdir(pickles_dir)) == len(get_all_repositories(sess)): return
    
    for repository in tqdm(get_all_repositories(sess), desc="Getting repositories"):
        if f"{repository.replace('/', '::')}.pickle" in listdir(pickles_dir): continue
        
        repository_def = Repository(repository, {})
        
        for workflow in tqdm(get_repository_workflows(repository, sess), desc=f"Getting the workflows from {repository}", leave=False):
            if Path(workflow).suffix != ".yaml" and Path(workflow).suffix != ".yml": continue
            
            if workflow not in repository_def.workflows:
                repository_def.workflows[workflow] = Workflow({})
            
            for commit in tqdm(get_workflow_commits(f"{repository}/{workflow}", sess), desc=f"Getting the commits from {workflow}", leave=False):
                date: DateTime = commit[1]
                parsed = datetime(date.year, date.month, date.day, date.hour, date.minute, date.day)
                
                repository_def.workflows[workflow].commits[commit[0]] = Commit(
                    parsed,
                    get_commit_dependencies(f"{repository}/{workflow}/{commit[0]}", sess)
                )
            
        with open(join(dirname(abspath(__file__)), f"../../repositories/{repository.replace('/', '::')}.pickle"), "wb") as file:
            dump(repository_def, file, protocol=HIGHEST_PROTOCOL)
            

def pickle2repo(file_name: str) -> Repository:
    with open(join(dirname(abspath(__file__)), f"../../repositories/{file_name}.pickle"), "rb") as file:
        return load(file)
        
        
if __name__ == "__main__":
    repos2pickles()
