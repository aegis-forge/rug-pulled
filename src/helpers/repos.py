from os import listdir
from os.path import join, dirname, abspath, splitext, isdir

from .pickling import repos2pickles


def get_repo_names() -> list[str]:
    pickles_dir = join(dirname(abspath(__file__)), "../../repositories")

    if not isdir(pickles_dir): repos2pickles()
    if len(listdir(pickles_dir)) == 0: repos2pickles()

    return [splitext(pickle)[0].replace("::", "/") for pickle in listdir(pickles_dir)]
