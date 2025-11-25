from datetime import datetime
from os import listdir, mkdir
from os.path import abspath, dirname, isdir, join
from pathlib import Path
from pickle import HIGHEST_PROTOCOL, dump

from dotenv import dotenv_values
from neotime import DateTime
from tqdm import tqdm

from .helpers.queries import (
    connect,
    get_all_repositories,
    get_commit_dependencies,
    get_repository_workflows,
    get_workflow_commits,
)
from .models.neo import Commit, Repository, Workflow


def _get_repos():
    sess = connect(dotenv_values(join(dirname(abspath(__file__)), "../.env")))

    pickles_dir = join(dirname(abspath(__file__)), "../data/repositories")

    if not isdir(pickles_dir):
        mkdir(pickles_dir)
    if len(listdir(pickles_dir)) == len(get_all_repositories(sess)):
        quit()

    for repository in tqdm(get_all_repositories(sess), desc="Getting repositories"):
        if f"{repository.replace('/', '::')}.pickle" in listdir(pickles_dir):
            continue

        repository_def = Repository(repository, {})

        for workflow, filepath in tqdm(
            get_repository_workflows(repository, sess).items(),
            desc=f"Getting the workflows from {repository}",
            leave=False,
        ):
            if Path(workflow).suffix != ".yaml" and Path(workflow).suffix != ".yml":
                continue

            if workflow not in repository_def.workflows:
                repository_def.workflows[workflow] = Workflow(filepath, {})

            for commit in tqdm(
                get_workflow_commits(f"{repository}/{workflow}", sess),
                desc=f"Getting the commits from {workflow}",
                leave=False,
            ):
                date: DateTime = commit[1]
                parsed = datetime(
                    date.year, date.month, date.day, date.hour, date.minute, date.day
                )

                repository_def.workflows[workflow].commits[commit[0]] = Commit(
                    parsed,
                    get_commit_dependencies(
                        f"{repository}/{workflow}/{commit[0]}", sess
                    ),
                )

        with open(
            join(
                dirname(abspath(__file__)),
                f"../data/repositories/{repository.replace('/', '::')}.pickle",
            ),
            "wb",
        ) as file:
            dump(repository_def, file, protocol=HIGHEST_PROTOCOL)
            file.close


if __name__ == "__main__":
    _get_repos()
