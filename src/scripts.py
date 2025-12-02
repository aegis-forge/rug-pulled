from datetime import datetime
from os import listdir, mkdir
from os.path import abspath, dirname, isdir, join
from pathlib import Path
from pickle import HIGHEST_PROTOCOL, dump

from dotenv import dotenv_values
from neotime import DateTime
from numpy import nan
from pandas import DataFrame, read_csv
from tqdm import tqdm

from src.helpers.repos import pickle2repo

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


def _get_dataset():
    df_lines: list[dict[str, str | datetime]] = []
    filepath: str = join(dirname(abspath(__file__)), "../data/repositories")
    commit_dates: list[datetime] = []

    for file in tqdm(listdir(filepath)):
        repo: Repository = pickle2repo(file.removesuffix(".pickle"))

        for workflow_name, workflow in repo.workflows.items():
            for commit_name, commit in workflow.commits.items():
                for action_name, action in commit.dependencies["direct"].items():
                    dependencies = {
                        dep_name: dep
                        for dep_name, dep in commit.dependencies["indirect"].items()
                        if dep.parent == action_name
                    }

                    for dep_name, dep in dependencies.items():
                        for vulnerability in dep.vulnerabilities.keys():
                            df_lines.append(
                                {
                                    "repository": repo.name,
                                    "workflow": workflow_name,
                                    "commit": commit_name,
                                    "action": action_name,
                                    "action_u": str(action.uses),
                                    "action_v": action.version,
                                    "action_d": action.date,
                                    "dependency": dep_name,
                                    "dependency_v": dep.version,
                                    "vulnerability": vulnerability,
                                }
                            )
                        else:
                            df_lines.append(
                                {
                                    "repository": repo.name,
                                    "workflow": workflow_name,
                                    "commit": commit_name,
                                    "action": action_name,
                                    "action_u": str(action.uses),
                                    "action_v": action.version,
                                    "action_d": action.date,
                                    "dependency": dep_name,
                                    "dependency_v": dep.version,
                                    "vulnerability": "",
                                }
                            )
                else:
                    df_lines.append(
                        {
                            "repository": repo.name,
                            "workflow": workflow_name,
                            "commit": commit_name,
                            "action": "",
                            "action_u": "",
                            "action_v": "",
                            "action_d": "",
                            "dependency": "",
                            "dependency_v": "",
                            "vulnerability": "",
                        }
                    )
                
                commit_dates.append(commit.date)
            else:
                df_lines.append(
                    {
                        "repository": repo.name,
                        "workflow": workflow_name,
                        "commit": "",
                        "action": "",
                        "action_u": "",
                        "action_v": "",
                        "action_d": "",
                        "dependency": "",
                        "dependency_v": "",
                        "vulnerability": "",
                    }
                )

    print("Saving...")
    DataFrame(df_lines).to_csv(join(dirname(abspath(__file__)), "../data/dataset.csv"))
    DataFrame(commit_dates).to_csv(join(dirname(abspath(__file__)), "../data/commit_dates.csv"))
    print("DONE")


def _precompute_dataset_metrics():
    print("Loading CSV...")
    df: DataFrame = read_csv(join(dirname(abspath(__file__)), "../data/dataset.csv"))
    print("DONE\n")

    df_lines: list[dict[str, str | float | int]] = []

    def gen_line(
        el: str,
        min: float,
        max: float,
        mean: float,
        median: float,
        unique: float,
        total: int,
    ) -> dict[str, str | float | int]:
        return {
            "element": el,
            "min": min,
            "max": max,
            "mean": mean,
            "median": median,
            "unique": unique,
            "total": total,
        }

    rs = df["repo"].nunique()
    df_lines.append(gen_line("repos", nan, nan, nan, nan, nan, int(rs)))

    ws = df[["repo", "workflow"]].drop_duplicates().groupby(by=["repo"]).size()
    print(ws, "\n")
    cs = (
        df[["repo", "workflow", "commit"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow"])
        .count()
    )
    print(cs, "\n")
    acs = (
        df[["repo", "workflow", "commit", "action", "action_v", "action_u"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow", "commit"])
        .sum()
        .drop(["action", "action_v"], axis=1)
    )
    print(acs, "\n")
    acsv = (
        df[["repo", "workflow", "commit", "action", "action_v", "action_u"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow", "commit"])
        .sum()
        .drop(["action", "action_v"], axis=1)
    )
    print(acsv, "\n")
    ds = (
        df[["repo", "workflow", "commit", "action", "dependency"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow", "commit", "action"])
        .count()
    )
    print(ds, "\n")
    dsv = (
        df[["repo", "workflow", "commit", "action", "dependency", "dependency_v"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow", "commit", "action", "dependency"])
        .count()
    )
    print(dsv, "\n")
    vsc = (
        df[["repo", "workflow", "commit", "action", "dependency", "dependency_v"]]
        .drop_duplicates()
        .groupby(by=["repo", "workflow", "commit", "action", "dependency"])
        .count()
    )
    print(vsc, "\n")
    vsa = (
        df[["repo", "workflow", "commit", "action", "vulnerability"]]
        .groupby(by=["repo", "workflow", "commit", "action"])
        .count()
    )
    print(vsa, "\n")
    vs = (
        df[["repo", "workflow", "commit", "action", "dependency", "vulnerability"]]
        .groupby(by=["repo", "workflow", "commit", "action", "dependency"])
        .count()
    )
    print(vs, "\n")

    for i, cat in enumerate(
        zip(
            [ws, cs, acs, acsv, ds, dsv, vsc, vsa, vs],
            [
                "workflow",
                "commit (per workflow)",
                "action (per commit)",
                "action version (per commit)",
                "dependency (per action)",
                "dependency version (per action)",
                "vulnerability (per commit)",
                "vulnerability (per action)",
                "vulnerability (per dependency)",
            ],
        )
    ):
        if i == 3:
            unique = (df["action"] + "@" + df["action_v"]).dropna().nunique()
        elif i == 5:
            unique = (df["dependency"] + "@" + df["dependency_v"]).dropna().nunique()
        else:
            unique = int(df[cat[1].split(" (")[0]].dropna().nunique())

        df_lines.append(
            gen_line(
                cat[1],
                int(cat[0].min()),
                int(cat[0].max()),
                round(float(cat[0].mean()), 2),
                int(cat[0].median()),
                unique,
                int(cat[0].sum()),
            )
        )

    print("Saving...")
    DataFrame(df_lines).set_index("element").to_csv(
        join(dirname(abspath(__file__)), "../data/dataset_stats.csv")
    )
    print("DONE")


if __name__ == "__main__":
    # _get_repos()
    _get_dataset()
    # _precompute_dataset_metrics()
