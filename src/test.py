# %%
from pandas import DataFrame, read_csv

df: DataFrame = read_csv("../data/dataset.csv")

# %%
df[["action", "action_d"]].drop_duplicates().groupby(by="action").count().to_csv("../data/actions_versions.csv")

# %%
