from os import listdir
from os.path import join, dirname, abspath, splitext
from pickle import load

from ..models.neo import Repository


def get_repo_names() -> list[str]:
    pickles_dir = join(dirname(abspath(__file__)), "../../data/repositories")
    pickle_files = [splitext(pickle)[0].replace("::", "/") for pickle in listdir(pickles_dir)]

    return pickle_files


def pickle2repo(file_name: str) -> Repository:
    with open(join(dirname(abspath(__file__)), f"../../data/repositories/{file_name}.pickle"), "rb") as file:
        return load(file)
