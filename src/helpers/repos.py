from os import listdir
from os.path import join, dirname, abspath, splitext

from .pickling import repos2pickles


def get_repo_names(env: dict[str, str]) -> list[str]:
    repos2pickles(env)
    
    pickles_dir = join(dirname(abspath(__file__)), "../../repositories")
    pickle_files = [splitext(pickle)[0].replace("::", "/") for pickle in listdir(pickles_dir)]

    return pickle_files
