# %%
from pandas import DataFrame, read_csv

df: DataFrame = read_csv("../data/dataset.csv")
# %%
action_versions = df[["repository", "workflow", "commit", "action", "action_v", "action_u"]].drop_duplicates()[
    ["action", "action_v", "action_u"]
].dropna()

# %%
action_versions[action_versions["action_v"].str.match(f"[A-z0-9]{40}")]["action_u"].sum()
# %%
df[["repository", "workflow", "commit", "action", "action_v", "action_u"]].drop_duplicates().dropna()[["action", "action_u"]].groupby(by="action").sum().to_csv("../data/actions.csv")

# %%
df[["repository", "workflow", "commit", "action", "action_v", "action_u"]].drop_duplicates().dropna()[["action", "action_v"]]
